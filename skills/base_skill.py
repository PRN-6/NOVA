class BaseSkill:

    @property
    def name(self) -> str:
        raise NotImplementedError
    
    @property
    def description(self) -> str:
        raise NotImplementedError
    
    @property
    def fast_intents(self) -> list[str]:
        raise NotImplementedError
    
    def execute(self,text: str) -> bool:
        raise NotImplementedError