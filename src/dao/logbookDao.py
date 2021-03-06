
from configuration import dbConnectionInfo
from db.DbSource import DbSource
from dataStructures import LogbookItem
from utils import getDayTimestamps


def _prepareCondition(address=None, icaoCode=None, registration=None):
    c1 = c2 = ''
    if icaoCode:
        c1 = f" AND l.location_icao = '{icaoCode}'"
    if registration:
        c2 = f" AND d.aircraft_registration = '{registration}'"
    cond = c1 + c2

    return cond


def listDepartures(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [], sortTsDesc=False):

    cond = _prepareCondition(address=address, icaoCode=icaoCode, registration=registration)

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.ts >= {startTs} AND l.ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.location_icao LIKE '{prefix}%'"
            if i < (len(icaoFilter) - 1):
                c += ' OR '
        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection() as c:

        strSql = f"""SELECT l.ts, l.address, l.address_type, l.aircraft_type, l.lat, l.lon, l.location_icao, 
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'T' AND (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL) {cond} {condTs} {condIcao}
                    ORDER by ts {sortTs} {condLimit};"""

        c.execute(strSql)

        rows = c.fetchall()
        for row in rows:
            (ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, devType, aircraftType, registration, cn) = row

            item = LogbookItem(address=address,
                               takeoff_ts=ts,
                               takeoff_lat=float(lat),
                               takeoff_lon=float(lon),
                               takeoff_icao=locationIcao,
                               landing_ts=0,
                               landing_lat=0,
                               landing_lon=0,
                               landing_icao=None,
                               flight_time=0,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType)

            records.append(item)

    return records


def listArrivals(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [], sortTsDesc=False):

    cond = _prepareCondition(address=address, icaoCode=icaoCode, registration=registration)

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.ts >= {startTs} AND l.ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.location_icao LIKE '{prefix}%'"
            if i < (len(icaoFilter)-1):
                c += ' OR '
        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection() as c:

        strSql = f"""SELECT l.ts, l.address, l.address_type, l.aircraft_type, l.lat, l.lon, l.location_icao, l.flight_time,
                    d.device_type,	d.aircraft_type, d.aircraft_registration, d.aircraft_cn 
                    FROM logbook_events AS l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id 
                    WHERE l.event = 'L' AND (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL) {cond} {condTs} {condIcao}
                    ORDER by ts {sortTs} {condLimit};"""

        c.execute(strSql)

        rows = c.fetchall()
        for row in rows:
            (ts, address, addrType, aircraftTypeCode, lat, lon, locationIcao, flightTime, devType, aircraftType, registration, cn) = row

            item = LogbookItem(address=address,
                               takeoff_ts=0,
                               takeoff_lat=0,
                               takeoff_lon=0,
                               takeoff_icao=None,
                               landing_ts=ts,
                               landing_lat=float(lat),
                               landing_lon=float(lon),
                               landing_icao=locationIcao,
                               flight_time=flightTime,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType)

            records.append(item)

    return records


def listFlights(address=None, icaoCode=None, registration=None, forDay=None, limit=None, icaoFilter: list = [], sortTsDesc=False, orderByCol='takeoff_ts'):

    c1 = c2 = ''
    if icaoCode:
        c1 = f" AND (l.takeoff_icao = '{icaoCode}' OR l.landing_icao = '{icaoCode}')"
    if registration:
        c2 = f" AND d.aircraft_registration = '{registration}'"
    cond = c1 + c2

    condTs = ''
    condLimit = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.takeoff_ts >= {startTs} AND l.landing_ts <= {endTs}"

    if limit:
        condLimit = f" limit {limit}"

    condIcao = ''
    if len(icaoFilter) > 0:
        c = ""
        for i, prefix in enumerate(icaoFilter):
            c += f"l.takeoff_icao LIKE '{prefix}%' OR l.landing_icao like '{prefix}%'"
            if i < (len(icaoFilter)-1):
                c += ' OR '

        condIcao += f" AND ({c})"

    sortTs = 'DESC' if sortTsDesc else 'ASC'

    records = list()

    with DbSource(dbConnectionInfo).getConnection() as c:

        strSql = f"""SELECT l.address, l.takeoff_ts, l.takeoff_lat, l.takeoff_lon, l.takeoff_icao, 
                    l.landing_ts, l.landing_lat, l.landing_lon, l.landing_icao, l.flight_time,
                    d.device_type, d.aircraft_type, d.aircraft_registration, d.aircraft_cn
                    FROM logbook_entries as l 
                    LEFT JOIN ddb AS d ON l.address = d.device_id
                    WHERE (d.tracked != false OR d.tracked IS NULL) AND (d.identified != false OR d.identified IS NULL) {cond} {condTs} {condIcao}
                    ORDER by {orderByCol} {sortTs} {condLimit};"""

        c.execute(strSql)

        rows = c.fetchall()
        for row in rows:
            (address, ts1, lat1, lon1, locationIcao1, ts2, lat2, lon2, locationIcao2, flightTime, devType, aircraftType, registration, cn) = row

            item = LogbookItem(address=address,
                               takeoff_ts=ts1 if ts1 else None,
                               takeoff_lat=float(lat1) if lat1 else None,
                               takeoff_lon=float(lon1) if lon1 else None,
                               takeoff_icao=locationIcao1 if locationIcao1 else None,
                               landing_ts=ts2,
                               landing_lat=float(lat2),
                               landing_lon=float(lon2),
                               landing_icao=locationIcao2,
                               flight_time=flightTime,
                               device_type=devType,
                               registration=registration,
                               cn=cn,
                               aircraft_type=aircraftType)

            records.append(item)

    return records


def getSums(registration, forDay=None, limit=None):
    cond = f" AND d.aircraft_registration='{registration}'"

    condTs = ''
    startTs, endTs = getDayTimestamps(forDay)
    if startTs and endTs:
        condTs = f" AND l.takeoff_ts >= {startTs} AND l.landing_ts <= {endTs}"

    numFlights = 0
    totalFlightTime = 0

    with DbSource(dbConnectionInfo).getConnection() as c:

        strSql = f"""SELECT COUNT(l.address) AS num, SUM(l.flight_time) AS time
                        FROM logbook_entries as l 
                        LEFT JOIN ddb AS d ON l.address = d.device_id
                        WHERE tracked = true AND identified = true {cond} {condTs}
                        ORDER by landing_ts desc;"""

        c.execute(strSql)

        row = c.fetchall()

        if row:
            numFlights = row[0][0]
            totalFlightTime = row[0][1]    # [s]

    return numFlights, totalFlightTime
