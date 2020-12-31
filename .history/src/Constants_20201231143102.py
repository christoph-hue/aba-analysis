GLOB_Z = 'global-z-score'
EXPR_LVL = 'expression_level'
VALUE_COLUMNS = [EXPR_LVL,GLOB_Z] 

DATAFRAME_CACHE = "cache\\data-frames\\"

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
            cache=True, # the semantics of this function are a bit weird. providing True means: add it to the cache,
            url="http://api.brain-map.org/api/v2/data/query.json?criteria=model::PlaneOfSection"
        )

  def getPlaneOfSections(self):
    return self.PlaneOfSections

allenSdkHelper = AllenSdkHelper()

PlaneOfSections = allenSdkHelper.getPlaneOfSections()