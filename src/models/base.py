# Import all models here so SQLAlchemy metadata is fully populated
from src.models.cart import Cart, CartItem  # noqa: F401
from src.models.coupon import Coupon  # noqa: F401
from src.models.order import Order, OrderItem  # noqa: F401
from src.models.product import Product  # noqa: F401
from src.models.review import Review  # noqa: F401
from src.models.user import User  # noqa: F401
