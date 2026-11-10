"""Interactive CRUD CLI shared in style by both storage implementations."""
from database import PeeweeDataManager

ENTITIES = {
 '1': ('users','Users', [('username','Username'),('email','Email'),('password_hash','Password hash'),('role','Role')]),
 '2': ('devices','Devices', [('hostname','Hostname'),('ip_address','IP address'),('device_type','Device type'),('status','Status'),('location','Location')]),
 '3': ('services','Services', [('device_id','Device ID (existing)'),('service_name','Service name'),('port','Port'),('status','Status')]),
 '4': ('monitor_logs','Security events', [('device_id','Device ID (existing)'),('status_code','Status code'),('latency_ms','Latency ms'),('checked_at','Checked at (blank = now)')]),
 '5': ('security_alerts','Alerts', [('device_id','Device ID (existing)'),('alert_type','Alert type'),('severity','Severity'),('description','Description'),('created_at','Created at (blank = now)')]),
}


def cast_fields(entity, values):
    for key in ('device_id','port','status_code','latency_ms'):
        if key in values: values[key] = int(values[key])
    for key in ('checked_at','created_at'):
        if values.get(key, None) == '': values.pop(key)
    return values


def ask_id():
    return int(input('Record ID: ').strip())


def run():
    manager = PeeweeDataManager()
    try:
        while True:
            print('\n=== NetSec Monitor ===')
            for key, (_, label, _) in ENTITIES.items(): print(f'{key}. {label}')
            print('0. Exit')
            choice = input('Select: ').strip()
            if choice == '0': break
            if choice not in ENTITIES: print('Invalid selection.'); continue
            entity, label, fields = ENTITIES[choice]
            while True:
                print(f'\n-- {label} --\n1. Create  2. List  3. View  4. Update  5. Delete  0. Back')
                action = input('Select: ').strip()
                try:
                    if action == '0': break
                    if action == '1':
                        values = {key: input(f'{prompt}: ').strip() for key, prompt in fields}
                        values = cast_fields(entity, values)
                        row = manager.create(entity, **values)
                        print('Created:', row)
                    elif action == '2':
                        for row in manager.list(entity): print(row)
                    elif action == '3':
                        print(manager.get(entity, ask_id()) or 'Record not found.')
                    elif action == '4':
                        record_id = ask_id()
                        values = {key: val for key, prompt in fields
                                  if (val := input(f'{prompt} (blank = keep): ').strip()) != ''}
                        values = cast_fields(entity, values)
                        print(manager.update(entity, record_id, **values) or 'Record not found.')
                    elif action == '5':
                        print('Deleted.' if manager.delete(entity, ask_id()) else 'Record not found.')
                    else: print('Invalid selection.')
                except (ValueError, TypeError) as exc:
                    print(f'Invalid input: {exc}')
                except Exception as exc:
                    print(f'Operation failed: {exc}')
    finally:
        manager.close()

if __name__ == '__main__': run()
