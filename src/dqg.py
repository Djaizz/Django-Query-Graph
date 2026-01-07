"""Django Query Graph."""


from __future__ import annotations

from typing import LiteralString, Self

from django.db.models.base import Model as DjangoModel
from django.db.models.query import Prefetch, QuerySet as DjangoQuerySet

from polymorphic.models import PolymorphicModel as DjangoPolymorphicModel

from neomodel.sync_.node import StructuredNode as NeoNode
from neomodel.sync_.match import NodeSet as NeoNodeSet


__all__: tuple[LiteralString] = ('DjangoQueryGraph',)


PK_FIELD_NAME: LiteralString = 'pk'


type ModelOrNode = DjangoModel | NeoNode
type QueryOrNodeSet = DjangoQuerySet | NeoNodeSet


class DjangoQueryGraph:
    """Django Query Graph."""

    def __init__(  # pylint: disable=too-many-locals
            self,
            ModelOrNodeClass: type[ModelOrNode], /,
            *non_many_related_field_names: str,
            ORDER: bool | str | list[str] | tuple[str, ...] | None = True,
            **fk_and_many_related_field_names_and_graphs: Self) -> None:
        """Initialize Django Query Graph."""
        if PK_FIELD_NAME in non_many_related_field_names:
            assert not ORDER, \
                f'*** ORDERING MUST BE OFF WHEN "{PK_FIELD_NAME}" PRESENT ***'

        # pylint: disable=invalid-name
        self.ModelOrNodeClass: type[ModelOrNode] = ModelOrNodeClass

        all_non_many_related_field_names: set[str] = \
            {field.name
             for field in ModelOrNodeClass._meta.fields}
        all_non_many_related_field_names.add(PK_FIELD_NAME)

        _non_many_related_field_names: set[str] = \
            set(non_many_related_field_names)

        assert not (_invalid_field_names :=
                    _non_many_related_field_names.difference(
                        all_non_many_related_field_names)), \
            ValueError(f'*** INVALID FIELD NAMES: {_invalid_field_names} ***')

        _overlapping_field_names = _non_many_related_field_names.intersection(
                                    fk_and_many_related_field_names_and_graphs)
        assert not _overlapping_field_names, \
            f'*** OVERLAPPING FIELD NAMES: {_overlapping_field_names} ***'

        fk_mqgs = {}
        self.many_related_mqgs = {}

        for fk_or_many_related_field_name, fk_or_many_related_mqg \
                in fk_and_many_related_field_names_and_graphs.items():
            assert isinstance(fk_or_many_related_mqg, DjangoQueryGraph), \
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

                self.ModelOrNodeClass.__name__,

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

    def query_or_node_set(self, init: QueryOrNodeSet | None = None) -> QueryOrNodeSet:  # noqa: E501
        """Django Query Set or NeoModel Node Set."""
        qs: QueryOrNodeSet = init or self.ModelOrNodeClass.objects

        if self.select_related:
            qs: QueryOrNodeSet = qs.select_related(*self.select_related)

        # .only(...) seems to mess up PolymorphicModel
        if not issubclass(self.ModelOrNodeClass, DjangoPolymorphicModel | NeoNode):  # noqa: E501
            qs: QueryOrNodeSet = qs.only(*self.field_names)

        if self.order:
            if isinstance(self.order, list | tuple):
                qs: QueryOrNodeSet = qs.order_by(*self.order)

            else:
                assert self.order is True

        else:
            qs: QueryOrNodeSet = qs.order_by()

        if self.many_related_mqgs:
            qs: QueryOrNodeSet = \
                qs.prefetch_related(
                    *(Prefetch(
                        lookup=many_related_field_name,
                        queryset=many_related_mqg.query_set())
                      for many_related_field_name, many_related_mqg
                        in self.many_related_mqgs.items()))

        return qs
