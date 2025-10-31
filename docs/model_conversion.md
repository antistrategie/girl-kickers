# Converting MMD Models to KHM in 3DS MAX

WORK IN PROGRESS.

This guide goes through the process of taking MMD models, re-texturing and re-rigging them, and exporting them to KHM format.

https://www.moddb.com/downloads/3ds-max-2010-pmx-importer1

Remove reflections from all materials:
```3ds
for mat in sceneMaterials where classof mat == Multimaterial do for sub in mat.materialList where sub != undefined and classof sub == PhysicalMaterial do (sub.base_weight = 1.0; sub.reflectivity = 0.0; sub.roughness = 1.0; sub.metalness = 0.0)
```
