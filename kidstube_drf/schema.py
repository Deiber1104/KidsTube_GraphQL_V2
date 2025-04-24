import graphene
import apps.backend.schema

class Query(apps.backend.schema.Query, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query)