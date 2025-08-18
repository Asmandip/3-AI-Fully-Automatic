from dash_extensions.enrich import DashProxy as OriginalDashProxy

class PatchedDashProxy(OriginalDashProxy):
    def __init__(self, *args, **kwargs):
        # async_callbacks প্যারামিটার থাকলে তা সরিয়ে ফেলুন
        kwargs.pop("async_callbacks", None)
        super().__init__(*args, **kwargs)
