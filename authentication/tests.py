# tests.py

# هذا الملف يجمع كل الاختبارات في مكان واحد.
# مشغل اختبارات Django يكتشف تلقائيًا الاختبارات في الملفات التي يبدأ اسمها بـ `test`.

from .tests_models import *
from .tests_services import *
from .tests_views import *
from .tests_security import *
from .tests_performance import *

print("All test modules loaded.")

