# exception_logging_middleware_v0_0_2.py by Rachel Bush. Date finished: 
# PROGRAM ID: exception_logging_middleware.py (_v0_0_2) / Exception logging middleware
# REMARKS: This file contains middleware for processing exceptions. It creates a record in the database for each exception.
# VERSION REMARKS: 

import traceback
from Meowseum.models import ExceptionRecord

class ExceptionLoggingMiddleware(object):
    def process_exception(self, request, exception):
        new_record = ExceptionRecord()
        # Store the part of the URL after the domain name, including the querystring.
        new_record.path = request.get_full_path()
        new_record.exception_type = exception.__class__.__name__
        new_record.exception_message = str(exception)
        new_record.traceback = ''.join(traceback.format_exception(exception.__class__, exception, exception.__traceback__))[0:100000]
        new_record.save()
        return None
