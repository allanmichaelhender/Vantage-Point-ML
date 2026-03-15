from pydantic import BaseModel, ConfigDict

class Players(BaseModel):
    player_id: str
    player_name: str

    # Pydantic expects dictonaries, this line allows Pydnatic to use object attributes to extract variables
    model_config = ConfigDict(from_attributes=True)