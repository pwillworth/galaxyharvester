use swgresource;
INSERT INTO tResourceType VALUES ('armophous_hoth_1','Hothian Type 1 Amorphous Gemstone','mineral','gemstone_armophous',1,2,1,1000,0,0,1,1000,0,0,600,1000,1,600,0,0,1,1000,1,1000,1,1000,1,1000,'gemstone','gemstone',11);
INSERT INTO tResourceType VALUES ('crystalline_hoth_1','Hothian Type 1 Crystalline Gemstone','mineral','gemstone_crystalline',1,2,1,1000,0,0,1,1000,0,0,600,1000,1,600,0,0,1,1000,1,1000,1,1000,1,1000,'gemstone','gemstone',11);
INSERT INTO tResourceType VALUES ('armophous_hoth_2','Hothian Type 2 Amorphous Gemstone','mineral','gemstone_armophous',1,2,1,1000,0,0,1,1000,0,0,600,1000,1,600,0,0,1,1000,1,1000,1,1000,1,1000,'gemstone','gemstone',11);
INSERT INTO tResourceType VALUES ('crystalline_hoth_2','Hothian Type 2 Crystalline Gemstone','mineral','gemstone_crystalline',1,2,1,1000,0,0,1,1000,0,0,600,1000,1,600,0,0,1,1000,1,1000,1,1000,1,1000,'gemstone','gemstone',11);
UPDATE tResourceType SET enterable=0 WHERE resourceType IN ('armophous_hoth','crystalline_hoth');

