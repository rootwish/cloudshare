#encoding: utf-8
import os

import services.customer
import sources.industry_id
from baseapp.datadbs import *

MED_needed = sources.industry_id.needed_medical
AI_needed = sources.industry_id.needed_ai


customer = services.customer.Customer(SVC_CO_REPO, SVC_CV_REPO, SVC_MULT_PEO,
                                      'willendare', 'willendare')

PRJ_LIST = customer.projects.values()
