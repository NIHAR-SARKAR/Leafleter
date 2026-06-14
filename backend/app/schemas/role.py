"""Role and permission Pydantic schemas."""

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """Base permission fields."""

    name: str = Field(..., max_length=100)
    resource: str = Field(..., max_length=50)
    action: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=500)


class PermissionCreate(PermissionBase):
    """Permission creation payload."""

    pass


class PermissionInDB(PermissionBase):
    """Permission database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int


class PermissionShort(BaseModel):
    """Compact permission reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class RoleBase(BaseModel):
    """Base role fields."""

    name: str = Field(..., max_length=100)
    description: str | None = Field(None, max_length=500)


class RoleCreate(RoleBase):
    """Role creation payload."""

    permission_ids: list[int] = []


class RoleUpdate(BaseModel):
    """Role update payload."""

    name: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    permission_ids: list[int] | None = None


class RoleInDB(RoleBase):
    """Role database response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_system: bool
    organization_id: int | None


class RolePublic(RoleInDB):
    """Public role response with permissions."""

    permissions: list[PermissionShort]


class RoleShort(BaseModel):
    """Compact role reference."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
