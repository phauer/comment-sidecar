FROM php:8.5-apache

RUN apt-get update &&\
    apt-get install -y locales &&\
    locale-gen en_US.UTF-8
ENV LANG='en_US.UTF-8'

# configure PHP environment and apache modules
RUN docker-php-ext-install mysqli pdo pdo_mysql
RUN cp /etc/apache2/mods-available/rewrite.load /etc/apache2/mods-enabled/rewrite.load

# mail() calls in PHP should end up in mhsendmail, which sends the mails to the mailhog container
RUN apt-get install --no-install-recommends --assume-yes --quiet ca-certificates curl git &&\
    rm -rf /var/lib/apt/lists/*
RUN curl -Lsf 'https://go.dev/dl/go1.22.5.linux-'$(dpkg --print-architecture)'.tar.gz' | tar -C '/usr/local' -xzf -
ENV PATH /usr/local/go/bin:$PATH
RUN GOBIN=/usr/bin go install github.com/mailhog/mhsendmail@latest
# PHP calls sendmail_path with `-t -i`, which current mhsendmail versions reject. So we drop the flags in a wrapper.
RUN printf '#!/bin/sh\nexec /usr/bin/mhsendmail --smtp-addr=mailhog:1025\n' > /usr/local/bin/sendmail-wrapper && chmod +x /usr/local/bin/sendmail-wrapper
RUN echo 'sendmail_path = /usr/local/bin/sendmail-wrapper' >> /usr/local/etc/php/php.ini

# xdebug 3
RUN pecl install xdebug && docker-php-ext-enable xdebug
RUN echo 'xdebug.mode=debug' >> /usr/local/etc/php/php.ini
RUN echo 'xdebug.client_port=9000' >> /usr/local/etc/php/php.ini
RUN echo 'xdebug.discover_client_host=1' >> /usr/local/etc/php/php.ini
# surface all warnings/deprecations during development and tests
RUN echo 'display_errors=On' >> /usr/local/etc/php/php.ini
RUN echo 'error_reporting=E_ALL' >> /usr/local/etc/php/php.ini
