from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    try:
        return dictionary.get(key)
    except Exception, e:
        return None
        
@register.filter
def check_difference(key, objs):
    try:
        difference_exists = False
        values = []
        for obj in objs:
            if obj.parameters is not None:
                value = obj.parameters.get(key)
            else:
                value = None
            values.append(value)
        for val in values:
            for val1 in values:
                if val != val1:
                    difference_exists = True
                    break
            if difference_exists:
                break
        if difference_exists:
            return True
        else:
            return False
    except Exception, e:
        return False
        
@register.filter
def extend_pgs(pgs, default):
    all_pgs = list(pgs)
    all_pgs.append(default)
    return all_pgs
