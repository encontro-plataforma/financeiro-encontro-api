from sqlalchemy import asc, desc


def apply_sort(query, model, sort: str, allowed_fields: dict, default_sort: str = None):
    # 🔥 aplica sort padrão se não vier nada
    if not sort and default_sort:
        sort = default_sort
        
    if not sort:
        return query

    orders = []

    for item in sort.split(","):
        try:
            field, direction = item.split(":")
        except ValueError:
            continue

        column = allowed_fields.get(field)

        if not column:
            continue

        if direction.lower() == "desc":
            orders.append(desc(column))
        else:
            orders.append(asc(column))

    if orders:
        return query.order_by(*orders)

    return query