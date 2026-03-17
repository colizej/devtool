from django import template

register = template.Library()


@register.filter
def split(value, delimiter=','):
    return value.split(delimiter)


@register.filter
def get_issue_count(issue_type, issues):
    """Возвращает количество issues определённого типа из списка."""
    return sum(1 for i in issues if i.issue_type == issue_type)
