from pydantic import BaseModel


class RepositoryInfo(BaseModel):
    owner: str
    name: str
    full_name: str
    default_branch: str
    clone_url: str
