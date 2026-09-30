from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd
from sqlalchemy import text

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
if str(RAIZ_PROYECTO) not in sys.path:
    sys.path.insert(0, str(RAIZ_PROYECTO))

from decision_hub.app_db import engine

ORIGEN = "SEED_DECISION_HUB"
RNG = np.random.default_rng(20260724)

DDL = """
CREATE TABLE IF NOT EXISTS comercial.dim_producto_operativa (
    id_producto VARCHAR(20) PRIMARY KEY,
    vida_util_dias INTEGER NOT NULL,
    lead_time_reposicion_dias INTEGER NOT NULL,
    stock_seguridad_dias NUMERIC(10,2) NOT NULL,
    capacidad_semanal_unidades NUMERIC(18,2) NOT NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'SEED_DECISION_HUB'
);

CREATE TABLE IF NOT EXISTS comercial.fact_stock_snapshot (
    fecha DATE NOT NULL,
    id_producto VARCHAR(20) NOT NULL,
    stock_disponible_unidades NUMERIC(18,2) NOT NULL,
    stock_seguridad_unidades NUMERIC(18,2) NOT NULL,
    demanda_promedio_diaria NUMERIC(18,4) NOT NULL,
    doh NUMERIC(18,4),
    pct_vida_util_consumida NUMERIC(18,4),
    riesgo_stock VARCHAR(20) NOT NULL,
    venta_perdida_estimada NUMERIC(18,2) NOT NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'SEED_DECISION_HUB',
    PRIMARY KEY (fecha, id_producto)
);

CREATE TABLE IF NOT EXISTS comercial.fact_forecast (
    semana_inicio DATE NOT NULL,
    id_producto VARCHAR(20) NOT NULL,
    forecast_unidades NUMERIC(18,2) NOT NULL,
    stock_seguridad_unidades NUMERIC(18,2) NOT NULL,
    capacidad_disponible_unidades NUMERIC(18,2) NOT NULL,
    brecha_forecast_stock NUMERIC(18,2) NOT NULL,
    riesgo_semana VARCHAR(20) NOT NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'SEED_DECISION_HUB',
    PRIMARY KEY (semana_inicio, id_producto)
);

CREATE TABLE IF NOT EXISTS comercial.fact_promociones (
    id_promocion BIGSERIAL PRIMARY KEY,
    id_producto VARCHAR(20) NOT NULL,
    id_cliente BIGINT,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    descuento_pct NUMERIC(10,4) NOT NULL,
    unidades_antes NUMERIC(18,2) NOT NULL,
    unidades_promocion NUMERIC(18,2) NOT NULL,
    unidades_despues NUMERIC(18,2) NOT NULL,
    unidades_incrementales NUMERIC(18,2) NOT NULL,
    margen_incremental NUMERIC(18,2) NOT NULL,
    coste_promocion NUMERIC(18,2) NOT NULL,
    roi_promocional NUMERIC(18,4),
    indice_canibalizacion NUMERIC(18,4),
    resultado_promocion VARCHAR(30) NOT NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'SEED_DECISION_HUB'
);

CREATE TABLE IF NOT EXISTS comercial.fact_costos_operativos_pedido (
    id_pedido VARCHAR(80) PRIMARY KEY,
    id_cliente BIGINT NOT NULL,
    fecha_pedido DATE NOT NULL,
    ventas_netas NUMERIC(18,2) NOT NULL,
    margen_bruto NUMERIC(18,2) NOT NULL,
    peso_kg NUMERIC(18,2) NOT NULL,
    distancia_km NUMERIC(18,2) NOT NULL,
    coste_logistico NUMERIC(18,2) NOT NULL,
    acuerdos_comerciales NUMERIC(18,2) NOT NULL,
    penalizaciones_demora NUMERIC(18,2) NOT NULL,
    margen_neto_real NUMERIC(18,2) NOT NULL,
    margen_neto_real_pct NUMERIC(18,4),
    coste_por_entrega NUMERIC(18,2) NOT NULL,
    coste_por_kg NUMERIC(18,4),
    es_deficitario BOOLEAN NOT NULL,
    origen VARCHAR(40) NOT NULL DEFAULT 'SEED_DECISION_HUB'
);
"""


def col(df: pd.DataFrame, opciones: list[str], obligatoria: bool = True) -> str | None:
    mapa = {str(c).lower(): str(c) for c in df.columns}
    for opcion in opciones:
        if opcion.lower() in mapa:
            return mapa[opcion.lower()]
    if obligatoria:
        raise KeyError(f"No se encontró {opciones}. Disponibles: {list(df.columns)}")
    return None


def crear_estructura() -> None:
    with engine.begin() as conn:
        for sentencia in [s.strip() for s in DDL.split(';') if s.strip()]:
            conn.execute(text(sentencia))


def limpiar() -> None:
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM comercial.fact_promociones WHERE origen=:o;
            DELETE FROM comercial.fact_forecast WHERE origen=:o;
            DELETE FROM comercial.fact_stock_snapshot WHERE origen=:o;
            DELETE FROM comercial.fact_costos_operativos_pedido WHERE origen=:o;
            DELETE FROM comercial.dim_producto_operativa WHERE origen=:o;
        """), {"o": ORIGEN})


def cargar():
    productos = pd.read_sql("SELECT * FROM comercial.dim_productos", engine)
    pedidos = pd.read_sql("SELECT * FROM comercial.fact_pedidos", engine)
    lineas = pd.read_sql("SELECT * FROM comercial.fact_lineas_pedido", engine)
    clientes = pd.read_sql("SELECT * FROM logistica.clientes", engine)
    return productos, pedidos, lineas, clientes


def preparar_detalle(pedidos, lineas):
    p_id, p_fecha, p_cliente = col(pedidos,["id_pedido"]), col(pedidos,["fecha_pedido"]), col(pedidos,["id_cliente"])
    l_id, l_prod = col(lineas,["id_pedido"]), col(lineas,["id_producto"])
    l_cant = col(lineas,["cantidad","unidades","cantidad_unidades"])
    l_venta = col(lineas,["importe_neto","ventas_netas","importe_total"])
    l_margen = col(lineas,["margen_bruto","margen"])
    l_peso = col(lineas,["peso_total_kg","peso_kg"], False)

    p = pedidos[[p_id,p_fecha,p_cliente]].copy()
    p.columns = ["id_pedido","fecha_pedido","id_cliente"]
    p["id_pedido"] = p["id_pedido"].astype(str)
    p["fecha_pedido"] = pd.to_datetime(p["fecha_pedido"]).dt.normalize()

    campos=[l_id,l_prod,l_cant,l_venta,l_margen] + ([l_peso] if l_peso else [])
    l=lineas[campos].copy().rename(columns={l_id:"id_pedido",l_prod:"id_producto",l_cant:"unidades",l_venta:"ventas_netas",l_margen:"margen_bruto", **({l_peso:"peso_kg"} if l_peso else {})})
    l["id_pedido"] = l["id_pedido"].astype(str)
    l["id_producto"] = l["id_producto"].astype(str)
    if "peso_kg" not in l:
        l["peso_kg"] = pd.to_numeric(l["unidades"], errors="coerce").fillna(0)*0.75
    for c in ["unidades","ventas_netas","margen_bruto","peso_kg"]:
        l[c]=pd.to_numeric(l[c],errors="coerce").fillna(0)
    return l.merge(p,on="id_pedido",how="inner")


def generar_dim(productos, detalle):
    pid=col(productos,["id_producto"])
    categoria=col(productos,["categoria"],False)
    dias=max(1,(detalle["fecha_pedido"].max()-detalle["fecha_pedido"].min()).days+1)
    demanda=detalle.groupby("id_producto",as_index=False)["unidades"].sum()
    demanda["demanda_diaria"]=demanda["unidades"]/dias
    campos=[pid]+([categoria] if categoria else [])
    d=productos[campos].copy().rename(columns={pid:"id_producto"})
    d["id_producto"]=d["id_producto"].astype(str)
    d=d.merge(demanda[["id_producto","demanda_diaria"]],on="id_producto",how="left")
    d["demanda_diaria"]=d["demanda_diaria"].fillna(.5).clip(lower=.25)
    d["vida_util_dias"]=RNG.integers(30,121,len(d))
    d["lead_time_reposicion_dias"]=RNG.integers(1,8,len(d))
    d["stock_seguridad_dias"]=np.round(RNG.uniform(1.5,5,len(d)),2)
    d["capacidad_semanal_unidades"]=np.round(d["demanda_diaria"]*7*RNG.uniform(1.1,1.5,len(d)),2)
    d["origen"]=ORIGEN
    return d[["id_producto","vida_util_dias","lead_time_reposicion_dias","stock_seguridad_dias","capacidad_semanal_unidades","origen"]]


def generar_stock(productos, detalle, dim):
    pid=col(productos,["id_producto"])
    precio=col(productos,["precio_lista","precio"],False)
    p=productos[[pid]+([precio] if precio else [])].copy().rename(columns={pid:"id_producto", **({precio:"precio_unitario"} if precio else {})})
    p["id_producto"]=p["id_producto"].astype(str)
    if "precio_unitario" not in p: p["precio_unitario"]=100.0
    fechas=pd.date_range(detalle["fecha_pedido"].min(),detalle["fecha_pedido"].max(),freq="D")
    vd=detalle.groupby(["fecha_pedido","id_producto"],as_index=False)["unidades"].sum().rename(columns={"fecha_pedido":"fecha","unidades":"demanda_real"})
    bloques=[]
    for f in dim.merge(p,on="id_producto",how="left").itertuples(index=False):
        x=pd.DataFrame({"fecha":fechas}); x["id_producto"]=str(f.id_producto)
        v=vd[vd["id_producto"]==str(f.id_producto)][["fecha","id_producto","demanda_real"]]
        x=x.merge(v,on=["fecha","id_producto"],how="left"); x["demanda_real"]=x["demanda_real"].fillna(0)
        media=max(.25,float(x["demanda_real"].mean()))
        x["demanda_promedio_diaria"]=pd.Series(media*RNG.normal(1,.18,len(x)).clip(.45,1.75)).rolling(14,min_periods=1).mean().to_numpy()
        seg = (
            x["demanda_promedio_diaria"]
            * float(f.stock_seguridad_dias)
        )

        # Distribución objetivo de cobertura
        u = RNG.random(len(x))

        doh_objetivo = np.empty(len(x))

        # 10 % - Riesgo crítico
        mask = u < 0.10
        doh_objetivo[mask] = RNG.uniform(
            0.2, 4.9, mask.sum()
        )

        # 15 % - Riesgo moderado
        mask = (u >= 0.10) & (u < 0.25)
        doh_objetivo[mask] = RNG.uniform(
            5.0, 9.9, mask.sum()
        )

        # 65 % - Cobertura saludable
        mask = (u >= 0.25) & (u < 0.90)
        doh_objetivo[mask] = RNG.uniform(
            10.0, 30.0, mask.sum()
        )

        # 10 % - Exceso de inventario
        mask = u >= 0.90
        doh_objetivo[mask] = RNG.uniform(
            30.1, 45.0, mask.sum()
        )

        stock = (
            x["demanda_promedio_diaria"].to_numpy()
            * doh_objetivo
        )

        x["stock_seguridad_unidades"] = np.round(seg, 2)

        x["stock_disponible_unidades"] = np.round(
            np.maximum(stock, 0),
            2
        )
        x["doh"]=x["stock_disponible_unidades"]/x["demanda_promedio_diaria"]
        x["pct_vida_util_consumida"]=x["doh"]/float(f.vida_util_dias)
        x["riesgo_stock"] = np.select(
            [
                x["doh"] < 5,
                x["doh"] < 10,
                x["doh"] <= 30,
            ],
            [
                "CRITICO",
                "MODERADO",
                "BAJO",
            ],
            default="EXCESO"
        )

        crit = x["doh"] < 5

        perd=np.maximum(x["demanda_promedio_diaria"]-x["stock_disponible_unidades"],0)
        x["venta_perdida_estimada"]=np.where(crit,perd*float(f.precio_unitario),0)
        x["origen"]=ORIGEN; bloques.append(x)
    r=pd.concat(bloques,ignore_index=True); r["fecha"]=pd.to_datetime(r["fecha"]).dt.date
    return r[["fecha","id_producto","stock_disponible_unidades","stock_seguridad_unidades","demanda_promedio_diaria","doh","pct_vida_util_consumida","riesgo_stock","venta_perdida_estimada","origen"]]


def generar_forecast(stock,dim):
    x=stock.copy(); x["fecha"]=pd.to_datetime(x["fecha"]); x["semana_inicio"]=(x["fecha"]-pd.to_timedelta(x["fecha"].dt.weekday,unit="D")).dt.normalize()
    s=x.groupby(["semana_inicio","id_producto"],as_index=False).agg(demanda_media=("demanda_promedio_diaria","mean"),stock_seguridad_unidades=("stock_seguridad_unidades","mean"))
    s=s.merge(dim[["id_producto","capacidad_semanal_unidades"]],on="id_producto",how="left")
    s["forecast_unidades"]=np.round(s["demanda_media"]*7*RNG.uniform(.9,1.25,len(s)),2)
    s["capacidad_disponible_unidades"]=np.round(s["capacidad_semanal_unidades"]*RNG.uniform(.88,1.08,len(s)),2)
    s["brecha_forecast_stock"]=np.round(s["forecast_unidades"]-s["stock_seguridad_unidades"],2)
    s["riesgo_semana"]=np.select([s["forecast_unidades"]>s["capacidad_disponible_unidades"],s["brecha_forecast_stock"]>0],["CRITICO","MODERADO"],default="BAJO")
    s["semana_inicio"]=s["semana_inicio"].dt.date; s["origen"]=ORIGEN
    return s[["semana_inicio","id_producto","forecast_unidades","stock_seguridad_unidades","capacidad_disponible_unidades","brecha_forecast_stock","riesgo_semana","origen"]]


def generar_promociones(productos,clientes,detalle):
    pid=col(productos,["id_producto"]); cid=col(clientes,["id_cliente"])
    prods=productos[pid].astype(str).tolist(); clis=clientes[cid].dropna().astype(int).tolist(); n=min(max(15,int(len(prods)*.35)),len(prods))
    inicio_hist=detalle["fecha_pedido"].min(); fin_hist=detalle["fecha_pedido"].max(); rango=max(31,(fin_hist-inicio_hist).days-20)
    filas=[]
    for prod in RNG.choice(prods,size=n,replace=False):
        ini=inicio_hist+pd.Timedelta(days=int(RNG.integers(20,rango))); fin=min(ini+pd.Timedelta(days=int(RNG.integers(7,15))),fin_hist)
        d=detalle[detalle["id_producto"]==str(prod)]; unidades=max(1.,d["unidades"].sum()); precio=d["ventas_netas"].sum()/unidades; margen_u=d["margen_bruto"].sum()/unidades
        antes=max(20.,unidades/6*RNG.uniform(.8,1.2)); desc=float(RNG.uniform(.1,.3)); elast=float(RNG.uniform(.8,2.8)); can=float(RNG.uniform(0,.55))
        promo=antes*(1+desc*elast); despues=antes*(1-can); incr=promo+despues-2*antes; coste=promo*precio*desc; margen=incr*margen_u; roi=margen/coste if coste else np.nan
        resultado="DESTRUYE_VALOR" if roi<0 else "BAJO_RETORNO" if roi<.25 else "RENTABLE"
        filas.append({"id_producto":str(prod),"id_cliente":int(RNG.choice(clis)) if clis else None,"fecha_inicio":ini.date(),"fecha_fin":fin.date(),"descuento_pct":round(desc,4),"unidades_antes":round(antes,2),"unidades_promocion":round(promo,2),"unidades_despues":round(despues,2),"unidades_incrementales":round(incr,2),"margen_incremental":round(margen,2),"coste_promocion":round(coste,2),"roi_promocional":round(roi,4),"indice_canibalizacion":round(can,4),"resultado_promocion":resultado,"origen":ORIGEN})
    return pd.DataFrame(filas)


def generar_costos(pedidos,detalle):
    pid=col(pedidos,["id_pedido"]); ontime=col(pedidos,["es_on_time"],False); intentos=col(pedidos,["numero_intentos"],False)
    r=detalle.groupby(["id_pedido","id_cliente","fecha_pedido"],as_index=False).agg(ventas_netas=("ventas_netas","sum"),margen_bruto=("margen_bruto","sum"),peso_kg=("peso_kg","sum"))
    extras=pedidos[[pid]+[c for c in [ontime,intentos] if c]].copy().rename(columns={pid:"id_pedido"}); extras["id_pedido"]=extras["id_pedido"].astype(str); r=r.merge(extras,on="id_pedido",how="left")
    n=len(r); r["peso_kg"]=r["peso_kg"].clip(lower=1); r["distancia_km"]=np.round(RNG.gamma(2.5,7,n).clip(2,65),2)
    coste=220+r["distancia_km"]*18+r["peso_kg"]*2.6
    if intentos: coste+=(pd.to_numeric(r[intentos],errors="coerce").fillna(1).clip(lower=1)-1)*180
    demora=(~r[ontime].fillna(True).astype(bool)) if ontime else pd.Series(False,index=r.index)
    r["coste_logistico"]=np.round(coste,2); r["acuerdos_comerciales"]=np.round(r["ventas_netas"]*RNG.uniform(.015,.075,n),2)
    r["penalizaciones_demora"]=np.round(np.where(demora,r["ventas_netas"]*RNG.uniform(.005,.03,n),0),2)
    r["margen_neto_real"]=np.round(r["margen_bruto"]-r["coste_logistico"]-r["acuerdos_comerciales"]-r["penalizaciones_demora"],2)
    r["margen_neto_real_pct"]=np.where(r["ventas_netas"]!=0,r["margen_neto_real"]/r["ventas_netas"],np.nan); r["coste_por_entrega"]=r["coste_logistico"]; r["coste_por_kg"]=r["coste_logistico"]/r["peso_kg"]; r["es_deficitario"]=r["margen_neto_real"]<0; r["fecha_pedido"]=pd.to_datetime(r["fecha_pedido"]).dt.date; r["origen"]=ORIGEN
    return r[["id_pedido","id_cliente","fecha_pedido","ventas_netas","margen_bruto","peso_kg","distancia_km","coste_logistico","acuerdos_comerciales","penalizaciones_demora","margen_neto_real","margen_neto_real_pct","coste_por_entrega","coste_por_kg","es_deficitario","origen"]]


def guardar(df,tabla):
    schema,nombre=tabla.split('.')
    df.to_sql(nombre,engine,schema=schema,if_exists='append',index=False,method='multi',chunksize=1000)
    print(f"[OK] {tabla}: {len(df):,} filas")


def main():
    crear_estructura(); limpiar(); productos,pedidos,lineas,clientes=cargar(); detalle=preparar_detalle(pedidos,lineas)
    dim=generar_dim(productos,detalle); guardar(dim,'comercial.dim_producto_operativa')
    stock=generar_stock(productos,detalle,dim); guardar(stock,'comercial.fact_stock_snapshot')
    forecast=generar_forecast(stock,dim); guardar(forecast,'comercial.fact_forecast')
    guardar(generar_promociones(productos,clientes,detalle),'comercial.fact_promociones')
    guardar(generar_costos(pedidos,detalle),'comercial.fact_costos_operativos_pedido')
    print('\nSeed Decision Hub finalizado correctamente.')


if __name__ == '__main__':
    main()
