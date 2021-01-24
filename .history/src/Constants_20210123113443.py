GLOB_Z = 'global-z-score'
EXPR_LVL = 'expression_level'
VALUE_COLUMNS = [EXPR_LVL,GLOB_Z] 

DATAFRAME_CACHE = "cache\\data-frames\\"

GENE_LIST = ["Gabra1", "Gabra2", "Gabra4", "Gabra5", "Gabrb1", "Gabrb2", "Gabrb3", "Gabrd", "Gabrg2", "Gabrg3"]
AGGREGATION_FUNCTIONS = ['min', 'max', 'mean', 'var']
HEMISPHERE_SCOPES = ['left', 'right', 'both']
STRUCTURE_LEVELS = [l for l in range(0,10)]

from allensdk.api.queries.rma_api import RmaApi
from allensdk.api.cache import Cache
import Utils

class AllenSdkHelper:
  def __init__(self):
    self.rma = RmaApi() 

        # the cache_writeer allows us to easily cache the results
    self.cache_writer = Cache()

    self.PlaneOfSections = self.cache_writer.wrap(
            self.rma.json_msg_query,
            path=Utils.makedir(f'cache\\models') + '\\PlaneOfSection.json',
            cache=False, # the semantics of this function are a bit weird. providing True means: add it to the cache,
            url="http://api.brain-map.org/api/v2/data/query.json?criteria=model::PlaneOfSection,rma::options[num_rows$eqall]"
        )

  def getPlaneOfSections(self):
    return self.PlaneOfSections

allenSdkHelper = AllenSdkHelper()

PlaneOfSections = {x['id']: x['name'] for x in allenSdkHelper.getPlaneOfSections()} 