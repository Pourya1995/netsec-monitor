"""Flask CRUD application for NetSec Monitor."""
from datetime import datetime
import os
from flask import Flask, abort, flash, redirect, render_template, request, url_for
from peewee import IntegrityError, DoesNotExist
from models import database, initialize_database, User, Device, Service, SecurityEvent, Alert, Incident

ENTITIES = {
 "users": {"title":"Users", "model":User, "fields":[("username","Username","text",True),("email","Email","email",True),("password_hash","Password hash (optional)","text",False),("role","Role","text",True)]},
 "devices": {"title":"Devices", "model":Device, "fields":[("hostname","Hostname","text",True),("ip_address","IP address","text",True),("device_type","Device type","text",True),("status","Status","text",True),("location","Location","text",False)]},
 "services": {"title":"Services", "model":Service, "fields":[("device_id","Device","fk_device",True),("service_name","Service name","text",True),("port","Port","number",True),("status","Status","text",True)]},
 "security-events": {"title":"Security events", "model":SecurityEvent, "table":"monitor_logs", "fields":[("device_id","Device","fk_device",True),("status_code","Status code","number",True),("latency_ms","Latency (ms)","number",True),("checked_at","Checked at","datetime",False)]},
 "alerts": {"title":"Alerts", "model":Alert, "fields":[("device_id","Device","fk_device",True),("alert_type","Alert type","text",True),("severity","Severity","select_severity",True),("description","Description","textarea",False),("created_at","Created at","datetime",False)]},
 "incidents": {"title":"Incidents", "model":Incident, "fields":[("alert_id","Related alert","fk_alert",True),("assigned_user_id","Assigned user","fk_user",False),("title","Title","text",True),("status","Status","select_incident",True),("created_at","Created at","datetime",False)]},
}

def create_app(test_config=None):
 app=Flask(__name__)
 app.config.update(SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-only-change-me"), DATABASE_AUTO_INIT=True)
 if test_config: app.config.update(test_config)
 @app.before_request
 def _db_open():
  if database.is_closed(): database.connect(reuse_if_open=True)
  if app.config["DATABASE_AUTO_INIT"]: database.create_tables([User,Device,Service,SecurityEvent,Alert,Incident], safe=True)
 @app.teardown_request
 def _db_close(exc):
  if not database.is_closed(): database.close()
 @app.context_processor
 def _nav(): return {"entities":ENTITIES}
 @app.route("/")
 def index():
  counts={key:cfg["model"].select().count() for key,cfg in ENTITIES.items()}
  recent_alerts=Alert.select().order_by(Alert.created_at.desc()).limit(5)
  return render_template("dashboard.html",counts=counts,recent_alerts=recent_alerts)
 @app.route("/<entity>/")
 def list_records(entity):
  cfg=ENTITIES.get(entity)
  if not cfg: abort(404)
  q=request.args.get("q","").strip(); query=cfg["model"].select()
  # Search text columns safely through ORM; numeric/fk fields are excluded.
  text_cols=[getattr(cfg["model"], f[0]) for f in cfg["fields"] if f[2] in ("text","email","textarea")]
  if q and text_cols:
   from functools import reduce
   from operator import or_
   query=query.where(reduce(or_, [col.contains(q) for col in text_cols]))
  rows=list(query.order_by(cfg["model"].id.desc()))
  return render_template("list.html",entity=entity,cfg=cfg,rows=rows,search=q)
 @app.route("/<entity>/new",methods=["GET","POST"])
 @app.route("/<entity>/<int:record_id>/edit",methods=["GET","POST"])
 def edit_record(entity,record_id=None):
  cfg=ENTITIES.get(entity)
  if not cfg: abort(404)
  model=cfg["model"]; obj=model.get_or_none(model.id==record_id) if record_id else None
  if record_id and not obj: abort(404)
  if request.method=="POST":
   values={}
   try:
    for name,label,kind,required in cfg["fields"]:
     raw=request.form.get(name,"").strip()
     if required and not raw: raise ValueError(f"{label} is required.")
     if not raw:
      if kind=="datetime": continue
      if name=="password_hash": values[name]=""
      elif kind=="fk_user": values["assigned_user"] = None
      continue
     if kind in ("number",): values[name]=int(raw)
     elif kind=="datetime": values[name]=datetime.fromisoformat(raw)
     elif kind=="fk_device": values["device"]=Device.get_by_id(int(raw))
     elif kind=="fk_alert": values["alert"]=Alert.get_by_id(int(raw))
     elif kind=="fk_user": values["assigned_user"]=User.get_by_id(int(raw))
     elif name=="password_hash": values[name]=raw
     else: values[name]=raw
    if obj:
     for key,val in values.items(): setattr(obj,key,val)
     obj.save()
     flash("Record updated successfully.","success")
    else:
     model.create(**values); flash("Record created successfully.","success")
    return redirect(url_for("list_records",entity=entity))
   except (ValueError,TypeError,IntegrityError,DoesNotExist) as exc:
    flash("Could not save record: "+(str(exc) or "please check the entered values."),"error")
  choices={"devices":list(Device.select().order_by(Device.hostname)),"alerts":list(Alert.select().order_by(Alert.id.desc())),"users":list(User.select().order_by(User.username))}
  return render_template("form.html",entity=entity,cfg=cfg,obj=obj,choices=choices)
 @app.route("/<entity>/<int:record_id>")
 def detail(entity,record_id):
  cfg=ENTITIES.get(entity)
  if not cfg: abort(404)
  obj=cfg["model"].get_or_none(cfg["model"].id==record_id)
  if not obj: abort(404)
  return render_template("detail.html",entity=entity,cfg=cfg,obj=obj)
 @app.post("/<entity>/<int:record_id>/delete")
 def delete_record(entity,record_id):
  cfg=ENTITIES.get(entity)
  if not cfg: abort(404)
  obj=cfg["model"].get_or_none(cfg["model"].id==record_id)
  if not obj: abort(404)
  obj.delete_instance(recursive=True); flash("Record deleted.","success")
  return redirect(url_for("list_records",entity=entity))
 @app.cli.command("init-db")
 def init_db_command():
  initialize_database(); print("NetSec Monitor database initialized.")
 return app

app=create_app()
if __name__=="__main__": app.run(debug=True)
