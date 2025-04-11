use swgresource;
ALTER TABLE tFavorites ADD INDEX IX_fav_type_item (favType, itemID);