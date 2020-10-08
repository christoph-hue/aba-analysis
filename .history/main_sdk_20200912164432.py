from allensdk.api.queries.ontologies_api import OntologiesApi
from allensdk.api.queries.grid_data_api  import GridDataApi

# http://help.brain-map.org/display/api/Atlas+Drawings+and+Ontologies


oapi = OntologiesApi()
structure_graph = oapi.get_structures_with_sets([1])  # 1 is the id of the adult mouse structure graph

# This removes some unused fields returned by the query
structure_graph = StructureTree.clean_structures(structure_graph)  

tree = StructureTree(structure_graph)
tree.parents([1011])