import logging

logger = logging.getLogger('myapp')


class TableCreator:
    def __init__(self, table_name):
        self._debug = False
        self.table_name = table_name
        self.columns = ''
        self.conn = None
        self.dbcursor = None

    def column_from_cls(self, cls):
        self.columns = ''
        instance = cls()
        for attr in vars(instance):
            name = attr
            if attr == 'id':
                name = 'id INTEGER PRIMARY KEY AUTOINCREMENT'
                self.columns += f"{name},"
                continue
            atrpythontype = type(getattr(instance, attr))
            sql_type = self.get_sql_type(atrpythontype)
            if sql_type != 'non_valid':
                self.columns += f"{name} {sql_type},"
        self.columns = self.columns[:-1]

    def save_object_to_table(self, obj, dbcursor=None):
        values = ''
        curcol = self.columns.split(',')
        curcol = curcol[1:]
        curcol = [x.split(' ')[0] for x in curcol]
        for column in curcol:
            value = getattr(obj, column)
            if type(value) == str:
                value = value.replace("'", "''")
            if type(value) == bool:
                if value:
                    value = 1
                else:
                    value = 0
            values += f"'{value}',"
        values = values[:-1]
        curcol = ','.join(curcol)
        sql_query = f"INSERT INTO {self.table_name} ({curcol}) VALUES ({values})"
        if self._debug:
            logger.debug(sql_query)

        dbcursor.execute(sql_query)
        obj.id = dbcursor.lastrowid

    def delete_object_from_table(self, obj, dbcursor=None):
        sql_query = f"DELETE FROM {self.table_name} WHERE id = {obj.id}"
        if self._debug:
            logger.debug(sql_query)
        dbcursor.execute(sql_query)

    def update_object_to_table(self, obj, dbcursor=None):
        values = ''
        curcol = self.columns.split(',')
        curcol = curcol[1:]
        curcol = [x.split(' ')[0] for x in curcol]
        for column in curcol:
            value = getattr(obj, column)
            if type(value) == str:
                value = value.replace("'", "''")
            if type(value) == bool:
                if value:
                    value = 1
                else:
                    value = 0
            values += f"{column} = '{value}',"
        values = values[:-1]
        sql_query = f"UPDATE {self.table_name} SET {values} WHERE id = {obj.id}"
        if self._debug:
            logger.debug(sql_query)
        dbcursor.execute(sql_query)

    def fill_object_from_table(self, obj, dbcursor=None):
        sql_query = f"SELECT * FROM {self.table_name} WHERE id = {obj.id}"
        if self._debug:
            logger.debug(sql_query)
        dbcursor.execute(sql_query)
        result = dbcursor.fetchone()
        curcol = self.columns.split(',')
        curcol = curcol[1:]
        curcol = [x.split(' ')[0] for x in curcol]
        for i, column in enumerate(curcol):
            setattr(obj, column, result[i + 1])

    def create_table(self, dbcursor):
        dbcursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{self.table_name}'")
        result = dbcursor.fetchone()
        if not result:
            dbcursor.execute(f"CREATE TABLE {self.table_name} ({self.columns})")

    def get_sql_type(self, atrpythontype):
        if atrpythontype == int:
            return 'INTEGER'
        if atrpythontype == str:
            return 'TEXT'
        if atrpythontype == float:
            return 'REAL'
        if atrpythontype == bool:
            return 'INTEGER'
        if atrpythontype == bytes:
            return 'BLOB'

        return 'non_valid'
