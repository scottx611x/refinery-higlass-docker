FROM gehlenborglab/higlass:v0.2.62

# Swap the "app" html with the main html to always provide the /app/ view
RUN cp /home/higlass/projects/higlass-website/app/index.html /home/higlass/projects/higlass-website/index.html

# Don't start nginx automatically. We'll start it manually after tilesets have been ingested
RUN sed -i '/\[program\:nginx\]/a autostart \= false' supervisord.conf

# We want higlass launcher to access the default viewconf relative to our current location
RUN sed -i 's@"#higlass","\/api@"#higlass","\.\/api@g' \
/home/higlass/projects/higlass-website/assets/scripts/hg-launcher.js

# Have the default view_conf fixture point to a url relative to our current location
RUN sed -i 's@"\/api\/v1",@"\.\/api\/v1"@g' \
/home/higlass/projects/higlass-server/default-viewconf-fixture.xml

# Remove public data source
RUN sed -i 's@"http://higlass.io/api/v1"@@g' \
/home/higlass/projects/higlass-server/default-viewconf-fixture.xml

# Replace `../` with `./` for script/img/css fetching
RUN sed -i 's@"\.\.\/@"\.\/@g' \
/home/higlass/projects/higlass-website/index.html

# Higlass currently has no favicon.png causing a 500 Error
RUN touch higlass-website/assets/images/favicon.png


COPY on_startup.py /home/higlass/projects/higlass-server
COPY refinery-settings.py /home/higlass/projects/higlass-server/higlass_server
ENV DJANGO_SETTINGS_MODULE="higlass_server.refinery-settings"

# Append to the supervisord.conf and set the priority of `on_startup.py` to
# be greater than the default of `999` so that it starts up after uwsgi processes. 
# Running the `ingest_tileset` Django management command requires things like db migrations to have been applied, 
# which the uwsgi stuff handles.
RUN ( echo; \
      echo "[program:on_startup]"; \
      echo "command = python /home/higlass/projects/higlass-server/on_startup.py"; \
      echo "priority = 1000"; ) \
    >> supervisord.conf