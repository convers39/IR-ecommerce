from django import template

register = template.Library()


@register.filter()
def num_range(num):
    """
    Use in template language to loop through numberic range
    """
    return range(num)
