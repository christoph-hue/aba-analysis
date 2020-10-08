from allensdk.api.queries.rma_api import RmaApi
from allensdk.api.cache import Cache

from types import SimpleNamespace

import numpy as np
import pandas as pd

from StructureMap import StructureMap

class HumanMicroarrayData:
    def __init__(self, geneAcronym):
        self.geneAcronym = geneAcronym
    
    # ok, now we got n probes with m expression-levels & z-scores
    # we also got m samples that describe which donor and which structure each expression-level stems from
    # we have to be aware that the expression-levels are retrieved from a probe, which represents a plane through the brain.
    # so if the plane of the probe is not cutting through a specific brain-region, then there are null-values present for the expression-level.
    # details: http://help.brain-map.org/display/humanbrain/API

    def transformExpressionData(self, expressionData):

        # https://docs.python.org/3/library/types.html#types.SimpleNamespace
        combined = SimpleNamespace()

        setattr(combined, 'samples', []) 
        setattr(combined, 'expression_levels', [])
        setattr(combined, 'z_scores', [])

        for probe in expressionData["probes"]:
            # https://stackoverflow.com/questions/30522724/take-multiple-lists-into-dataframe
            #combined.append((["human" for x in range(num_samples)], 
            combined.samples += expressionData["samples"]
            combined.expression_levels += probe["expression_level"]
            combined.z_scores += probe["z-score"]


        print('rows: ' + str(len(combined.expression_levels)))
        # https://stackoverflow.com/questions/29325458/dictionary-column-in-pandas-dataframe
        data = pd.DataFrame({"expression_level": combined.expression_levels, "z-score": combined.z_scores},
                                    dtype=np.float32) # setting this type is important for later aggregation. else, pandas throws an error for mean & var

        def unpack_dict_list(dict_list, attribute, prefix):
            return pd.DataFrame.from_dict([dict_list[i][attribute] for i in range(len(dict_list))]).add_prefix(prefix) # prefix to prevent naming conflicts

        # attributes with their respective prefix to prevent ambiguous column-names
        attributes = [("donor", ""), ("sample", "sample_"), ("structure", "structure_")] # , ("top_level_structure", "top_lvl_struct_")

        data = pd.concat([*[unpack_dict_list(combined.samples, attr[0], attr[1]) for attr in attributes], data], axis=1) # note that here, the * is the splat-operator

        # dropna is super slow, so we use this approach instead:
        data = data[data['expression_level'].notnull()]
        data = data[data['z-score'].notnull()]

        return data 

    def get(self, from_cache, aggregations): # load data once with use_cache = True, then change it to False to read it from disk instead of fetching it from the api
        # we use the RmaApi to query specific information, such as the section data sets of a specific gene
        # for docs, see: https://alleninstitute.github.io/AllenSDK/allensdk.api.queries.rma_api.html
        rma = RmaApi() 

        # the cache_writeer allows us to easily cache the results
        cache_writer = Cache()
        

        # https://alleninstitute.github.io/AllenSDK/examples.html
        # https://community.brain-map.org/t/allen-mouse-ccf-accessing-and-using-related-data-and-tools/359
        # https://github.com/AllenInstitute/AllenSDK/blob/master/allensdk/api/queries/image_download_api.py

        # accessing microarray-data?
        # https://github.com/benfulcher/AllenSDK
        # https://human.brain-map.org/microarray/search/show?exact_match=false&search_term=gabra4&search_type=gene
        # https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5777841/
        # http://help.brain-map.org/display/api/Connected+Services+and+Pipes

        # ok, so we don't need to do multiple requests to forward data from a model to a service, but simply use the pipe-concept:
        # http://help.brain-map.org/display/api/Service+Pipelines
        # e.g. this finds all probes for gabra4 and then queries the microarray-expression data for these probes. note that variables generated by a pipe are referenced by $variableName

        query = ("http://api.brain-map.org/api/v2/data/query.json?criteria="
                f"model::Probe,rma::criteria,gene[acronym$il{self.geneAcronym}],rma::options[num_rows$eqall],"
                "pipe::list[probes$eq'id'],"
                "service::human_microarray_expression[probes$eq$probes]")


        data = cache_writer.wrap(
                rma.json_msg_query,
                path='cache\\human-microarray-expression.json',
                cache=not from_cache, # the semantics of this function are a bit weird. providing True means: add it to the cache,
                url=query
            )
        
        structure_map = StructureMap(reference_space_key = 'annotation/ccf_2017', resolution = 200).get(structure_graph_id=10)
        
        data = self.transformExpressionData(data)

        # https://stackoverflow.com/questions/31528819/using-merge-on-a-column-and-index-in-pandas
        # https://stackoverflow.com/questions/45147100/pandas-drop-columns-with-all-nans
        data = data.merge(structure_map,  right_index=True, left_on="structure_id", how="left").dropna(axis=1, how='all')

        return data.groupby([col for col in data.columns if 'level_' in col])['expression_level','z-score'].agg(aggregations)

        

        