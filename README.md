# IR-ecommerce

## NOTICE: THIS SITE IS DEAD DUE TO AWS INVOICE. RIP🙏.

### Demo Website: [IREC](https://irec.xyz/)
Demo account (only view permission in admin page):

email: demo@email.com
password: demo123456

**NOTE**: 
USE TEST CREDIT CARD TO MAKE PAYMENT
4242 4242 4242 4242

Check [here](https://stripe.com/docs/testing) for more info.
### About This Project

This is a simple ecommerce project built mainly by Django Framework + few Javascript/jquery, using Bootstrap 4 template with Django template language.

As a hands-on project for a newbee developer (myself), if your are tired of writing those helloworld crap, looking for something more challenging to make use of your Django and overall web development skills, hope this project could be helpful as your reference.

Since I am exploring the right way to impelement those features, I am pretty sure there are many other better approaches. Please feel free to share your ideas and indicate my mistakes, which would be really really appreciated.

### Sample Photos 

- Home - searching, category, trending items

![home](_samples/1-min.png)

- Shop list - list items, sorting, searching, categorizing

![list](_samples/2-min.png)

- Item detail - add shopping cart, add wishlist, check reviews, related products

![detail](_samples/3-min.png)

- Shopping cart - item crud operation 

![cart](_samples/4-min.png)

- Checkout - select payment method, edit or add address 

![checkout-login](_samples/5-min.png)

- Guest checkout - add shipping address on checkout

![checkout-guest](_samples/6-min.png)

- Find order - guest retrieving order data, making payment/return item 

![find-order](_samples/7-min.png)

![find-order-detail](_samples/8-min.png)

- Account center - change profile and password, list watch history in watched order

![account](_samples/9-min.png)

- Account center orders - order status management, pay/refund/return etc, order detail, write review

![account-order](_samples/10-min.png)

![account-order-detail](_samples/11-min.png)

- Account center - shipping address management

![account-address](_samples/12-min.png)

![account-address-add](_samples/13-min.png)

- Account wishlist - list wishlisted items 

![account-wishlist](_samples/14-min.png)

- Account activation email - also use for changing account email and sending order status update to customer

![account-activate-email](_samples/15-min.png)

- Admin page - appearance, actions

![admin-home](_samples/17-min.png)

![admin-order](_samples/16-min.png)

### Features

- **account center**

  - account registration with email activation (also used in changing email address)
  - login with email address
  - remember login
  - change profile and password (based on ajax request)
  - manage recipient addresses (based on ajax request)
  - order management
  - write review and rate stars for ordered items
  - google recaptcha for login and register ([django-recaptcha](https://github.com/praekelt/django-recaptcha))

- **shop**

  - list and detail view for items
  - add/remove item to/from wishlist
  - save watch history
  - show related item on detail page
  - fulltext search (postgresql)
  - item list view filter by sorting, category and tags
  - item tags ([django-taggit](https://github.com/jazzband/django-taggit))
  - recursive category ([django-mptt](https://github.com/django-mptt/django-mptt))

- **shopping cart**

  - add item to shopping cart
  - CRUD operation on shopping cart page (based on ajax request)
  - guest checkout

- **order and payment**

  - payment with [Stripe Checkout](https://stripe.com/docs/payments/checkout)
  - status management ([django-fsm](https://github.com/viewflow/django-fsm)) (NOTE: this package is going to be deprecated soon, will transit to [viewflow](https://docs-next.viewflow.io/fsm/index.html) in the future)

- **customized admin**

  - use modern admin theme([django-simpleui](https://github.com/newpanjing/simpleui))
  - custom views and actions (shipping, cancel order, refund)
  - autocomplete search ([easy-select2](https://github.com/asyncee/django-easy-select2))

- **others**

  - testing with [factory_boy](https://github.com/FactoryBoy/factory_boy) and [faker](https://github.com/joke2k/faker)
  - rich text editor in admin page ([django-ckeditor](https://github.com/django-ckeditor/django-ckeditor))
  - use [Sentry](https://docs.sentry.io/platforms/python/guides/django/) for monitoring
  - deployment on EC2
  
  

### Tech Stack 

- Django (>=3.1)

- PostgresSQL

- Redis

  - web site caching
  - login session cache
  - message queue broker
  - shopping cart, watch history, wishlist database

- AWS S3

  - media file storage

- AWS SES (prod env only)

- Celery

  - async tasks
  - periodic tasks / cron jobs

- Docker

### Architect

![architect](_samples/architect.jpg) 

The project is deployed in an EC2 instance, and makes use of other AWS services such as S3 bucket for media file storage, RDS for postgres database, and SES for email sending.

For details on deployment please refer to this tutorial:

[TestDriven.io](https://testdriven.io/blog/django-docker-https-aws/)

### DB Design

![db-models](_samples/db-models.jpg) 

**NOTE**
All (except Category and User) models inherit from a base model which has 3 fields: 
created_at, updated_up, is_deleted

The relationship between Order and Payment could be 1to1 which is easier to manage, while on some EC sites there is an option to pay multiple orders together, here just leave as it is.

Other models such as Invoice, CancelRecord, RefundRecord are not implemented as those could be acheived on the Stripe dashboard. 

### Order State Management

![checkout](_samples/checkout-flow.jpg) 

The states of order is quite complecated, and varies depending on projects and developer. It was really a headache for me.

This chart is created based on some references and my trials and errors, might work for a small project, but definately could be improved and better.

The core idea is that the status of order and status of payment should be seperated as 2 fields (instead of 1 status field in the Order model, which did not work well), meanwhile intertwined with each other (dot line arrows), since the state of payment or order could be the signal or criteria to make actions to change either order or payment's state. To acheive those transitions between different states, works could be done by a user, an admin, or the system.

It is not necessary to add every ongoing state or every perfect tense state (which confused me a lot at the beginning), instead it should be decided based on a simple question: Do I need an action to make the transition here? In other words, if you found that you need 2 steps to acheive the next state, that probably means there should be one more state in the middle.

### How To Start (Local Env)

First clone the repository:

```shell
$ git clone https://github.com/convers39/IR-ecommerce.git
```

Setup your local env file, in my example, the project folder tree looks as below, the env file located in core folder. The default location recognized by docker-compose file is the same directory with docker-compose (in this case the root dir), make sure you set the right file path for env file.

```shell
.
├── LICENSE
├── README.md
├── _samples
├── apps
│   ├── __init__.py
│   ├── account
│   ├── cart
│   ├── order
│   └── shop
│       ├── __init__.py
│       ├── admin.py
│       ├── apps.py
│       ├── context_processors.py
│       ├── managers.py
│       ├── migrations
│       ├── models.py
│       ├── signals.py
│       ├── tasks.py
│       ├── templatetags
│       ├── tests
│       │   ├── __init__.py
│       │   ├── factory.py
│       │   ├── test_models.py
│       │   ├── test_urls.py
│       │   └── test_views.py
│       ├── urls.py
│       └── views.py
├── core
│   ├── __init__.py
│   ├── asgi.py
│   ├── celery.py
│   ├── env
│   │   ├── env.local
│   │   ├── env.prod
│   │   ├── env.prod.proxy-companion
│   │   ├── env.staging
│   │   ├── env.staging.proxy-companion
│   ├── settings
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── local.py
│   │   ├── prod.py
│   │   └── testing.py
│   ├── urls.py
│   └── wsgi.py
├── db
│   ├── __init__.py
│   └── base_model.py
├── docker-compose.yml
├── dockerfile
├── manage.py
├── media
├── requirements.txt
├── static
│   ├── css
│   ├── icons
│   ├── img
│   ├── js
│   └── vendor
└── templates
    ├── account
    ├── base.html
    ├── cart
    ├── index.html
    ├── order
    └── shop
```

Then you will need to write down credentials of database, mail server, AWS s3 bucket and Stripe API keys in your env file, and in your settings you can obtain those values, for instance: 

```python
# core/settings/base.py
# ...
# Mail server settings will be different depending on which mail service you use
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_FROM = os.environ.get('EMAIL_FROM')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# Use postgresql as database, SQLite is not tested, and fulltext search is not supported
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
    }
}

# AWS setting
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME')  # change to your region
AWS_S3_SIGNATURE_VERSION = os.environ.get('AWS_S3_SIGNATURE_VERSION')
AWS_S3_FILE_OVERWRITE = True # either true or false is ok

# stripe key
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
STRIPE_PUBLIC_KEY = os.environ.get('STRIPE_PUBLIC_KEY')
WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET')
```

Now build the image and compose up the containers, add `--build` flag to compose up when rebuild is needed.

```bash
$ docker build .
$ docker-compose -f docker-compose.yml up 
```

Start an empowered interactive shell in django container (provided by [django-extensions](https://github.com/django-extensions/django-extensions)), use the container name (django in this project)

```bash
$ docker exec -it <django> bash
$ python manage.py shell_plus
```

Access to Postgresql and Redis (Postgresql container is removed in prod setup as using AWS RDS for DB)

```bash
$ docker exec -it <pgdb> psql -U <username> <password>
```

```bash
$ docker exec -it <redis> sh
$ redis-cli
```

To run a test, specify a setting file (might run to errors with debug toolbar if not using testing settings, which forces to turn off DEBUG)

```bash
$ python manage.py test <appname> --settings=core.settings.testing
```

### Future Updates

Currently on plan:

- [x] guest shopping cart and checkout 
- [x] deployment a demo site + deployment setup
- [ ] image resize on upload
- [ ] language support for Chinese and Japanese
- [ ] filters on shop item list and account center
- [ ] third party Oauth login
- [ ] coupon apply on shopping cart page



------

##### Template credits: 

[BOOTSTRAP TEMPLE](https://bootstraptemple.com/p/bootstrap-ecommerce)

