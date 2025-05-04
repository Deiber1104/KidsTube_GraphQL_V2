import graphene
from django.db.models import Q
from graphene_django.types import DjangoObjectType
from .models import CustomUserModel, PlaylistModel, RestrictedUserModel, VideoModel

# ESTOS SON LOS TIPOS DE OBJETOS QUE GRAPHENE_DJANGO VA A UTILIZAR PARA MOSTRAR LOS DATOS EN LOS QUERYS
# ES COMO UN MAPEO (CONEXIÓN ENTRE LOS MODELOS Y GRAPHQL) 
class CustomUserType(DjangoObjectType):
    class Meta:
        model = CustomUserModel         # MODELO AL QUE APUNTA
        fields = "__all__"              # CAMPOS DISPONIBLES PARA LAS CONSULTAS (SE PUEDEN DEFINIR)


class RestrictedUserType(DjangoObjectType):
    class Meta:
        model = RestrictedUserModel
        fields = "__all__"


class PlaylistType(DjangoObjectType):
    class Meta:
        model = PlaylistModel
        fields = "__all__"


class VideoType(DjangoObjectType):
    class Meta:
        model = VideoModel
        fields = "__all__"


# TODOS LOS KEYS DEBEN ESTAR EN EL ENV

# DEFINICIÓN DE LOS QUERYS
class Query(graphene.ObjectType):

    # NOMBRE DE LOS QUERYS Y DE QUE SE VAN A COMPONER (TIPOS DE DATOS QUE DEBEN COINCIDIR CON LOS TIPOS DEFINIDOS ARRIBA)
    all_users = graphene.List(CustomUserType)
    user_by_id = graphene.Field(CustomUserType, user_id=graphene.String(required=True))

    all_restricted_users = graphene.List(
        RestrictedUserType,
        restricted_user=graphene.String()
    )
    restricted_user_by_id = graphene.Field(RestrictedUserType, restricted_id=graphene.String(required=True))

    all_playlists = graphene.List(
        PlaylistType,
        profile=graphene.String(),                          # ID of a RestrictedUser
        video_name=graphene.String(),
        video_desc=graphene.String()
    )
    playlists_by_user = graphene.List(
        PlaylistType,
        user_id=graphene.String(required=True)                  # ID del usuario principal
    )
    playlist_by_id = graphene.Field(PlaylistType, playlist_id=graphene.String(required=True))

    playlists_by_restricted_user = graphene.List(
        PlaylistType, 
        restricted_id=graphene.String(required=True)
    )

    all_videos = graphene.List(
        VideoType,
        user_id=graphene.String(required=True)
    )
    video_by_id = graphene.Field(VideoType, video_id=graphene.String(required=True))

    videos_by_playlist = graphene.List(
        VideoType,  # El tipo de objeto que estamos buscando (VideoType)
        playlist_id=graphene.String(required=True)  # El argumento será el ID de la playlist
    )

    search_videos = graphene.List(
        VideoType,
        search_term=graphene.String(required=True),  # Término de búsqueda
        restricted_id=graphene.String(required=True)  # ID del usuario restringido
    )

    def resolve_search_videos(self, info, search_term, restricted_id):
        search_term = search_term.lower()

        playlists = PlaylistModel.objects.filter(
            associated_profiles__restricted_id=restricted_id
        )

        queryset = VideoModel.objects.filter(
            playlists__in=playlists
        ).distinct()

        return queryset.filter(
            Q(name__icontains=search_term) | Q(description__icontains=search_term)
        )

    def resolve_videos_by_playlist(self, info, playlist_id):
        try:
            playlist = PlaylistModel.objects.get(playlist_id=playlist_id)
        except PlaylistModel.DoesNotExist:
            return None

        # Filtrar los videos asociados con la playlist
        return VideoModel.objects.filter(playlists=playlist)


    def resolve_playlists_by_restricted_user(self, info, restricted_id):
        return PlaylistModel.objects.filter(associated_profiles__restricted_id=restricted_id)

    def resolve_all_users(root, info):
        return CustomUserModel.objects.all()

    def resolve_user_by_id(root, info, user_id):
        try:
            return CustomUserModel.objects.get(pk=user_id)
        except CustomUserModel.DoesNotExist:
            return None
    
    def resolve_all_restricted_users(root, info, restricted_user=None):
        queryset = RestrictedUserModel.objects.select_related('restricted_user').all()

        if restricted_user:
            queryset = queryset.filter(restricted_user__user_id=restricted_user)

        return queryset

    def resolve_restricted_user_by_id(root, info, restricted_id):
        try:
            return RestrictedUserModel.objects.select_related('restricted_user').get(pk=restricted_id)
        except RestrictedUserModel.DoesNotExist:
            return None

    def resolve_all_playlists(root, info, profile=None, video_name=None, video_desc=None):
        queryset = PlaylistModel.objects.prefetch_related('associated_profiles', 'videos').all()

        if profile:
            queryset = queryset.filter(associated_profiles__restricted_id=profile)
        
        if video_name:
            queryset = queryset.filter(videos__name__icontains=video_name)
        
        if video_desc:
            queryset = queryset.filter(videos__description__icontains=video_desc)
        
        return queryset.distinct()
    
    def resolve_playlists_by_user(root, info, user_id):
        restricted_profiles = RestrictedUserModel.objects.filter(restricted_user__user_id=user_id)

        playlists = PlaylistModel.objects.filter(associated_profiles__in=restricted_profiles).distinct()

        return playlists

    def resolve_playlist_by_id(root, info, playlist_id):
        return PlaylistModel.objects.prefetch_related('associated_profiles').filter(pk=playlist_id).first()

    def resolve_all_videos(root, info, user_id):
        restricted_profiles = RestrictedUserModel.objects.filter(restricted_user__user_id=user_id)

        queryset = VideoModel.objects.filter(playlists__associated_profiles__in=restricted_profiles).distinct()

        return queryset

    


# CARGA TODOS LOS QUERYS Y SUS DEFINICIONES
schema = graphene.Schema(query=Query)


# https://docs.graphene-python.org/projects/django/en/latest/queries/