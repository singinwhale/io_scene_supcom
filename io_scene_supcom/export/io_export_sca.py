from bpy_extras.io_utils import ExportHelper
from bpy_types import Operator


class ExportScaOperator(Operator, ExportHelper):
    def invoke(self, context, _event):
        return super().invoke(context, _event)

    def check(self, _context):
        return super().check(_context)

