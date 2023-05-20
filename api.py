# -*- coding=utf-8
from bottle import Bottle, request, response, run
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text
from sqlalchemy.ext.automap import automap_base
from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
import env

def get_db():
    engine = create_engine(
        f"mysql+pymysql://{env.DB_USER}:{env.DB_PASSWORD}@"
        f"{env.DB_HOST}:{env.DB_PORT}/{env.DB_NAME}?charset=utf8mb4"
    )
    Base = automap_base()
    Base.prepare(engine, reflect=True)
    Base = automap_base()

    Base.prepare(engine, reflect=True)
    models = Base.classes

    Session = sessionmaker(bind=engine)
    
    return engine, models, Session

def get_tx_cos():
    config = CosConfig(Region=env.COS_REGION, SecretId=env.COS_SECRET_ID, SecretKey=env.COS_SECRET_KEY)
    client = CosS3Client(config)
    return client


def check_auth():
    auth = request.get_header('Authorization', '')
    expected_auth = 'Bearer ' + env.API_PASSWORD
    if auth != expected_auth:
        response.status = 401
        return {'code': 1, 'msg': 'Unauthorized'}
    return True

app = Bottle()

@app.post('/api/<table>')
def api_post(table):
    authok = check_auth()
    if authok != True:
        return authok

    data = request.json

    engine, models, Session = get_db()

    sess = Session(bind=engine)
    insert = []
    update = []
    for item in data:
        if item.get('id'):
            obj = sess.query(models[table]).filter_by(id=item['id']).first()
            if obj:
                for k, v in item.items():
                    setattr(obj, k, v)
                update.append({'id': obj.id})
        else:
            obj = models[table](**item)
            sess.add(obj)
            sess.flush()
            insert.append({'id': obj.id})

    sess.commit()

    return {'code': 0, 'msg': 'success', 'data': {'insert': insert, 'update': update}}

@app.get("/api/<table>/:id")
def get_by_id(table, id):
    authok = check_auth()
    if authok != True:
        return authok
    
    engine, models, Session = get_db()
    session = Session()
    model = models.get(table, None)
    if not model:
        response.status = 400
        return {
            "error": f"Table '{table}' not found."
        }

    result = session.query(model).filter_by(id=id).first()
    if result:
        response.status = 200
        return {
            "result": {col.name: getattr(result, col.name) for col in model.__table__.columns}
        }
    else:
        response.status = 404
        return {
            "error": f"Record not found."
        }

@app.get("/api/<table>")
def get_by_params(table):
    authok = check_auth()
    if authok != True:
        return authok

    engine, models, Session = get_db()

    session = Session()
    model = models.get(table, None)
    if not model:
        response.status = 400
        return {
            "error": f"Table '{table}' not found."
        }

    query = session.query(model)

    for key, value in request.query.items():
        if key in model.__table__.columns:
            query = query.filter(text(f"{key}='{value}'"))
        else:
            response.status = 400
            return {
                "error": f"Invalid query parameter '{key}'."
            }

    result = query.all()

    if result:
        response.status = 200
        return {
            "result": [
                {col.name: getattr(row, col.name) for col in model.__table__.columns} for row in result
            ]
        }
    else:
        response.status = 404
        return {
            "error": f"Record not found."
        }
    
@app.post("/api/files")
def upload_file():
    authok = check_auth()
    if authok != True:
        return authok

    file = request.files.get('file')
    path = request.forms.get('path')

    if not path:
        response.status = 400
        return {
            "error": "No path specified."
        }

    if not file:
        response.status = 400
        return {
            "error": "No file uploaded."
        }

    client = get_tx_cos()

    response = client.put_object(
        Bucket=env.COS_BUCKET,
        Body=file.file.read(),
        Key= path + "/" + file.filename,
        StorageClass='STANDARD',
        EnableMD5=False
    )

    return {
        "result": {
            "url": f"https://{env.COS_BUCKET}.cos.{env.COS_REGION}.myqcloud.com/{path}/{file.filename}"
        }
    }

if __name__ == '__main__':
    run(app, host='0.0.0.0', port=8080)