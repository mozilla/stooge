# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/

from __future__ import absolute_import

from celery import Celery

celery = Celery('proj',
             broker='amqp://',
             backend='amqp://',
             include=['stooge.scanner.tasks'])

celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    celery.start()
