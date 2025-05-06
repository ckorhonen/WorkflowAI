from core.storage.mongo.migrations.base import AbstractMigration


class AddOrgSlackAndHashedKeyIndicesMigration(AbstractMigration):
    async def apply(self):
        # Unique composite index on tenant and name fields
        await self._organization_collection.create_index(
            [
                ("api_keys.hashed_key", 1),
            ],
            name="unique_api_hashed_key",
            unique=True,
            partialFilterExpression={
                "api_keys.hashed_key": {"$exists": True},
            },
        )
        await self._drop_index_if_exists(self._organization_collection, "org_settings_api_key_index")

        await self._organization_collection.create_index(
            [("slack_channel_id", 1)],
            name="unique_slack_channel_id",
            unique=True,
            partialFilterExpression={"slack_channel_id": {"$exists": True}},
        )

    async def rollback(self):
        await self._drop_index_if_exists(self._organization_collection, "unique_api_hashed_key")

        await self._organization_collection.create_index(
            [("api_keys.hashed_key", 1)],
            name="org_settings_api_key_index",
            unique=True,
            background=True,
            partialFilterExpression={"api_keys": {"$exists": True}},
        )
        await self._drop_index_if_exists(self._organization_collection, "unique_slack_channel_id")
