import requests, json


class AuthenticationError(Exception):
    """Exception raised for errors in the input salary.

    Attributes:
        url -- url that didn't provide tokens
        message -- explanation of the error

    """

    def __init__(self, url, message):
        self.url = url
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.url} -> {self.message}'


class JWT_Session:
    """
    Каждый инстант класса хранит в себе креды и JWT токены для доступа к сервису,
    автоматически авторизовывается и подновляет токены по мере необходимости

    Аргументы конструктора класса
        * username - логин от сервиса
        * password - пароль от сервиса
        * obtain_tokens_url - урл, на который необходимо отправлять креды для получения refresh и access токенов
        * refresh_token_url - урл, на который необходимо отправлять refresh токен, для получения нового access токена
        * auth_field - поле заголовка запроса, в который подставляется access токен, по умолчанию 'Authorization'
        * auth_prefix - префикс, добавляемый перед access token в поле заголовка, по умолчанию 'Bearer '
        * content_type - значение заголовка Content-Type, по умолчанию 'application/json'

    """

    def __init__(self, username, password, obtain_tokens_url, refresh_token_url, auth_field='Authorization',
                 auth_prefix='Bearer ', content_type='application/json'):
        """
        Конструктор класса
        методом __obtain_jwt_tokens__() получает от сервера токены в обмен на предоставленные креды

        """
        self.username = username
        self.password = password
        self.obtain_tokens_url = obtain_tokens_url
        self.refresh_token_url = refresh_token_url
        self.__obtain_jwt_tokens__()
        self.content_type = content_type
        self.auth_prefix = auth_prefix
        self.auth_field = auth_field

    def __obtain_jwt_tokens__(self, message=None):
        """
        Получает пару access и refresh токенов с URL, предоставленного пользователем в аргументе obtain_tokens_url при создании инстанса класса
        Если сервер ответил не 200-ым кодом или не вернул токены в полях 'refresh' и 'access', выкидывает ошибку
        Сохраняет полученные access и refresh токены в атрибуты

        """
        r = requests.request(method='post', url=self.obtain_tokens_url,
                             data={'username': self.username, 'password': self.password})
        if r.status_code != 200:
            if message:
                message = '\n'.join([message,
                                     f"Failed to obtain jwt tokens from a provided URL, server responded with code {r.status_code}: {r.json()}"])
            raise AuthenticationError(url=self.obtain_tokens_url, message=message)
        r = r.json()
        refresh_token = r.get('refresh', None)
        access_token = r.get('access', None)
        if not refresh_token or not access_token:
            raise AuthenticationError(url=self.obtain_tokens_url,
                                      message=f"Failed to obtain jwt tokens from a provided URL, server returned {r.json()}")
        self.refresh_token = refresh_token
        self.access_token = access_token

    def __refresh_access_token__(self):
        """
        В обмен на refresh токен получает access токен с URL, предоставленного пользователем в аргументе refresh_token_url при создании инстанса класса
        Если сервер ответил:
            * 401 кодом - refresh токен устарел, вызывается метод __obtain_jwt_tokens__() c дополнительной информацией для возможной ошибки через аргумент message
            * не 401-ым и не 200-ым кодами - выкидывает ошибку
            * 200 кодом - забирает из ответа поле access, и обновляет его значение в атрибутах класса
                          если в запросе нет поля access или оно пустое, выкидывает ошибку

        """
        r = requests.request(method='post', url=self.refresh_token_url, data={'refresh': self.refresh_token})
        if r.status_code == 401:
            self.__obtain_jwt_tokens__(
                message=f"Failed to obtain jwt access token from a provided URL, server responded with code {r.status_code}: {r.json()}")
            r = requests.request(method='post', url=self.refresh_token_url, data={'refresh': self.refresh_token})
        elif r.status_code != 200:
            raise AuthenticationError(url=self.refresh_token_url,
                                      message=f"Failed to refresh access tokens from a provided URL, server returned {r.json()}")
        r = r.json()
        access_token = r.get('access', None)
        if not access_token:
            raise AuthenticationError(url=self.refresh_token_url,
                                      message=f"Failed to obtain jwt access token from a provided URL, server returned {r.json()}")
        self.access_token = access_token

    def request_with_token(self, method, url, extra_headers=None, body=False):
        """
        Каждый инстант класса хранит в себе креды и JWT токены для доступа к сервису,
        автоматически авторизовывается и подновляет токены по необходимости

        Аргументы:
            * method - тип запроса: 'get', 'post', 'put', 'patch', 'delete', 'options', всё стандартно, см. спецификацию HTTP
            * url - URL, на который нужно отправить запрос
            * extra_headers - пользовательские поля запроса в формате cловаря
            * body - тело запроса, по умолчанию False

        """
        headers = {f'{self.auth_field}': f'{self.auth_prefix}{self.access_token}', 'Content-Type': self.content_type}
        if not extra_headers:
            extra_headers = {}
        headers.update(extra_headers)
        r = requests.request(method=method, url=url, headers=headers, data=body)
        if r.status_code == 401:
            self.__refresh_access_token__()
            headers.update({f'{self.auth_field}': f'{self.auth_prefix}{self.access_token}'})
            r = requests.request(method=method, url=url, headers=headers, data=body)
        return r
