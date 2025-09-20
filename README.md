## таблица товаров
product_id: ulid  
name: str  
price: int  


## таблица заказов
order_id: ulid  
payment_id: str  
payment_status: str  
user_id: int  
created_at: datetime  
updated_at: datetime  


## таблица товаров_заказов
order_id: ulid  
product_id: ulid  
quantity: int  
price: int  
name: str

## DEPS
postgresql 15+  
python 3.1*

## ENVS
PG_HOST  
PG_USER  
PG_PASSWORD  
PG_PORT  
PG_DB  

BASE_URL  
LOGIN  
PASSWORD  
PAYMENT_CODE  
GROUP_CODE  

CREATE_TOKEN_URI  
VERIFY_TOKEN_URI  

REDIS_HOST  
REDIS_PASSWORD  
REDIS_PORT  
REDIS_DB  

ADMIN_SECRET_KEY   
ADMIN_USER_MODEL  
ADMIN_USER_MODEL_USERNAME_FIELD  

EKASSA_BASE_URL  
EKASSA_LOGIN  
EKASSA_PASSWORD  
EKASSA_PAYMENT_CODE  
EKASSA_GROUP_CODE  
EKASSA_CALLBACK_URL  

COMPANY_EMAIL  
COMPANY_INN  
COMPANY_WEBSITE_URL  

UKASSA_API_KEY  
UKASSA_SHOP_ID  
UKASSA_BASE_URL

## запуск для разработки
fastapi dev src/main.py

## запуск для деплоя
