"""narrativeos-cognitive — Zynd-registered NarrativeOS agent mesh wrapper.

Runs the full multi-agent pipeline (Narrative → Sentiment → Debate → Signal)
as a discoverable Zynd entity.
"""

from __future__ import annotations

import json
import os
import sys

from dotenv import load_dotenv
from zyndai_agent import AgentConfig, ZyndAIAgent, resolve_registry_url
from zyndai_agent.a2a.server import HandlerInput, TaskHandle

load_dotenv()

_config: dict = {}
if os.path.exists("agent.config.json"):
    with open("agent.config.json") as _f:
        _config = json.load(_f)


def run_analysis_pipeline(inbound: HandlerInput, task: TaskHandle) -> dict:
    try:
        from agents.graph.workflow import run_analysis
        from agents.models import NarrativeEvent

        events_data = inbound.message.content
        if isinstance(events_data, str):
            import json as _json
            events_data = _json.loads(events_data)

        raw_events = events_data if isinstance(events_data, list) else events_data.get("events", [events_data])
        events = [NarrativeEvent(**e) for e in raw_events]

        tickers = set()
        for e in events:
            tickers.update(e.ticker_mentions)
        primary = next(iter(tickers)) if tickers else None

        signal = run_analysis(events, primary)
        return signal.model_dump()

    except Exception as e:
        return task.fail(str(e))


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

    agent_config = AgentConfig(
        name=_config.get("name", "narrativeos-cognitive"),
        description=_config.get("description", "NarrativeOS multi-agent reasoning mesh"),
        version=_config.get("version", "0.1.0"),
        category=_config.get("category", "finance"),
        tags=_config.get("tags", ["narrative", "sentiment", "debate", "trading"]),
        server_host=_config.get("server_host", "0.0.0.0"),
        server_port=int(os.environ.get("ZYND_SERVER_PORT") or _config.get("server_port") or 5000),
        auth_mode=_config.get("auth_mode", "permissive"),
        registry_url=resolve_registry_url(from_config_file=_config.get("registry_url")),
        keypair_path=os.environ.get("ZYND_AGENT_KEYPAIR_PATH", _config.get("keypair_path")),
        entity_url=os.environ.get("ZYND_ENTITY_URL", _config.get("entity_url")),
        price=_config.get("price"),
        entity_pricing=_config.get("entity_pricing"),
        entity_index=_config.get("entity_index", 0),
        skills=_config.get("skills"),
        fqan=_config.get("fqan"),
    )

    zynd_agent = ZyndAIAgent(config=agent_config)
    zynd_agent.set_custom_agent(run_analysis_pipeline)
    zynd_agent.start()

    print("\nNarrativeOS Cognitive Mesh is running on Zynd")
    print(f"FQAN:    {agent_config.registry_url}/0xYuvi/narrativeos-cognitive")
    print(f"A2A URL: {zynd_agent.a2a_url}")
    print(f"Card:    {zynd_agent.card_url}")

    if sys.stdin.isatty():
        print("\nType 'exit' to quit\n")
        while True:
            try:
                cmd = input()
            except EOFError:
                break
            if cmd.lower() == "exit":
                break
        zynd_agent.stop()
    else:
        import signal
        signal.pause()
