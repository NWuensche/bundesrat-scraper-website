FROM python:3.8

RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
		postgresql-client \
	&& rm -rf /var/lib/apt/lists/*


WORKDIR /usr/src/app
COPY requirements.txt ./
RUN python3 -m venv getting-started
RUN python3 -m pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
RUN echo "yes" | python manage.py collectstatic
RUN python manage.py migrate
RUN python manage.py makemigrations
RUN python manage.py migrate 

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]
