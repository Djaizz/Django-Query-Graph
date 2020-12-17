from __future__ import annotations


__all__ = 'PK_FIELD_NAME', 'ModelQueryGraph'


from django.db.models.query import Prefetch, QuerySet

from typing import Optional, TypeVar


PK_FIELD_NAME = 'pk'


class ModelQueryGraph:
    _OrderingType = TypeVar('_OrderingType', bool, str, list, tuple)

    def __init__(
            self,
            ModelClass,
            *non_many_related_field_names: str,
            ORDER: Optional[_OrderingType] = True,
            **fk_and_many_related_field_names_and_graphs: ModelQueryGraph) \
            -> None:
        if PK_FIELD_NAME in non_many_related_field_names:
            assert not ORDER, \
                f'*** ORDERING MUST BE OFF WHEN "{PK_FIELD_NAME}" PRESENT ***'

        self.ModelClass = ModelClass

        all_non_many_related_field_names = \
            {field.name
             for field in ModelClass._meta.fields}
        all_non_many_related_field_names.add(PK_FIELD_NAME)

        _non_many_related_field_names = set(non_many_related_field_names)

        _invalid_field_names = _non_many_related_field_names.difference(
                                all_non_many_related_field_names)
        assert not _invalid_field_names, \
            f'*** INVALID FIELD NAMES: {_invalid_field_names} ***'

        _overlapping_field_names = _non_many_related_field_names.intersection(
                                    fk_and_many_related_field_names_and_graphs)
        assert not _overlapping_field_names, \
            f'*** OVERLAPPING FIELD NAMES: {_overlapping_field_names} ***'

        fk_mqgs = {}
        self.many_related_mqgs = {}

        for fk_or_many_related_field_name, fk_or_many_related_mqg \
                in fk_and_many_related_field_names_and_graphs.items():
            assert isinstance(fk_or_many_related_mqg, ModelQueryGraph), \
                '*** VALUE ASSOCIATED WITH FIELD ' \
                f'"{fk_or_many_related_field_name}" NOT A ModelQueryGraph ***'

            if fk_or_many_related_field_name in \
                    all_non_many_related_field_names:
                fk_mqgs[fk_or_many_related_field_name] = \
                    fk_or_many_related_mqg

            else:
                self.many_related_mqgs[fk_or_many_related_field_name] = \
                    fk_or_many_related_mqg

        self.select_related = tuple(fk_mqgs)
        self.field_names = non_many_related_field_names

        for fk_field_name, fk_mqg in fk_mqgs.items():
            self.select_related += \
                tuple(f'{fk_field_name}__{fk_model_select_related}'
                      for fk_model_select_related in
                      fk_mqg.select_related)

            self.field_names += \
                tuple(f'{fk_field_name}__{fk_model_field_name}'
                      for fk_model_field_name in
                      fk_mqg.field_names)

            for fk_many_related_field_name, fk_many_related_mqg \
                    in fk_mqg.many_related_mqgs.items():
                self.many_related_mqgs[
                        f'{fk_field_name}__{fk_many_related_field_name}'] = \
                    fk_many_related_mqg

        if ORDER:
            if ORDER is True:
                self.order = True

            else:
                if isinstance(ORDER, str):
                    self.order = ORDER,

                else:
                    assert isinstance(ORDER, (list, tuple))

                    self.order = ORDER

        else:
            self.order = None

    def __repr__(self) -> str:
        return '{}{}\nONLY({}){}{}'.format(

                self.ModelClass.__name__,

                f"\nSELECT_RELATED({', '.join(self.select_related)})"
                if self.select_related
                else '',

                ', '.join(self.field_names),

                f"\nORDER_BY({', '.join(self.order)})"
                if isinstance(self.order, (list, tuple))
                else '',

                '\nPREFETCH_RELATED(\n{}\n)'.format(
                    '\n\n'.join(
                        f'{many_related_field_name}: {many_related_mqg}'
                        for many_related_field_name, many_related_mqg
                        in self.many_related_mqgs.items()))
                    if self.many_related_mqgs
                    else '')

    __str__ = __repr__

    def query_set(
            self,
            init: Optional[QuerySet] = None) \
            -> QuerySet:
        qs = self.ModelClass.objects \
            if init is None \
            else init

        if self.select_related:
            qs = qs.select_related(*self.select_related)

        qs = qs.only(*self.field_names)

        if self.order:
            if isinstance(self.order, (list, tuple)):
                qs = qs.order_by(*self.order)

            else:
                assert self.order is True

        else:
            qs = qs.order_by()

        if self.many_related_mqgs:
            qs = qs.prefetch_related(
                    *(Prefetch(
                        lookup=many_related_field_name,
                        queryset=many_related_mqg.query_set())
                      for many_related_field_name, many_related_mqg
                        in self.many_related_mqgs.items()))

        return qs
