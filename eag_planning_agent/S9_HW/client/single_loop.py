from modules.perception import create_perception_engine
from modules.decision import create_decision_engine
from modules.action import execute_with_decision_result
from modules.perception import PerceptionResult
from modules.decision import DecisionResult

query = "What is the sum of 25 and 37?"

chat_history = []


async def call_perception_engine(query: str, chat_history: list):
    perception_engine = await create_perception_engine()
    perception_result = await perception_engine.analyze_query(query, chat_history)
    return perception_result


async def call_decision_engine(perception_result: PerceptionResult):
    decision_engine = await create_decision_engine()
    decision_result = await decision_engine.analyze_decision_from_perception(
        perception_result
    )
    return decision_result


async def call_action_engine(query: str, decision_result: DecisionResult):
    action_result = await execute_with_decision_result(query, decision_result)
    return action_result


if __name__ == "__main__":
    import asyncio
    import dataclasses
    import json

    print("Executing perception engine...")
    perception_result = asyncio.run(call_perception_engine(query, chat_history))
    print(f"Perception result: {perception_result}")
    print(f"Perception result in json: {perception_result.model_dump_json()}")
    print(f"Perception result in dict: {perception_result.model_dump()}")
    print("--------------------------------")

    print("Executing decision engine...")
    decision_result = asyncio.run(call_decision_engine(perception_result))
    print(f"Decision result: {decision_result}")
    print(f"Decision result in json: {decision_result.model_dump_json()}")
    print(f"Decision result in dict: {decision_result.model_dump()}")
    print("--------------------------------")

    print("Executing action engine...")
    action_result = asyncio.run(call_action_engine(query, decision_result))
    print(f"Action result: {action_result}")

    # ActionResult is a dataclass, not a Pydantic model, so use dataclasses.asdict
    print(
        f"Action result in json: {json.dumps(dataclasses.asdict(action_result), indent=2, default=str)}"
    )
    print(f"Action result in dict: {dataclasses.asdict(action_result)}")
    print("--------------------------------")
