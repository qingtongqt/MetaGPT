from metagpt.actions.action import Action
from metagpt.roles.role import Role
from metagpt.logs import logger
from ConsensusMaker import MakeConsensus


class ShowResult(Action):
    async def run(self, final_code: str):
        logger.info(f"final code:\n{final_code}")


class ResultMaker(Role):
    name: str = "Leo"
    profile: str = "Result Maker"
    goal: str = "Receive the final result and output"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_actions([ShowResult])
        self._watch([MakeConsensus])

    def _act(self):
        final_code = self.latest_observed_msg.content
        self.todo.run(final_code)
        return
