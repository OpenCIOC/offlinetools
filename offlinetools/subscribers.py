# =================================================================
# Copyright (C) 2011 Community Information Online Consortium (CIOC)
# http://www.cioc.ca
# Developed By Katherine Lambacher / KCL Custom Software
# If you did not receive a copy of the license agreement with this
# software, please contact CIOC via their website above.
#==================================================================


def add_renderer_globals(event):
    request = event['request']
    if not request:
        return
    event['_'] = request.translate
    event['localizer'] = request.localizer
    event['renderer'] = getattr(getattr(request,'model_state',None),'renderer', None)

