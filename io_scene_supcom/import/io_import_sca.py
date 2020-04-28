from bpy_extras.io_utils import ImportHelper
from bpy_types import Operator


class ImportScaOperator(Operator, ImportHelper):

    def invoke(self, context, _event):
        return super().invoke(context, _event)

    def check(self, _context):
        return super().check(_context)
