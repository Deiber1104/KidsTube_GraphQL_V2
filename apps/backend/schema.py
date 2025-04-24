import graphene
from graphene_django.types import DjangoObjectType
from .models import CustomUserModel, PlaylistModel, RestrictedUserModel, VideoModel

class CustomUserType(DjangoObjectType):
    class Meta:
        model = CustomUserModel
        fields = "__all__"



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


class Query(graphene.ObjectType):
    all_users = graphene.List(CustomUserType)
    user_by_id = graphene.Field(CustomUserType, user_id=graphene.String(required=True))

    all_restricted_users = graphene.List(RestrictedUserType)
    restricted_user_by_id = graphene.Field(RestrictedUserType, restricted_id=graphene.String(required=True))

    all_playlists = graphene.List(
        PlaylistType,
        profile=graphene.String(),  # ID of a RestrictedUser
        video_name=graphene.String(),
        video_desc=graphene.String()
    )
    playlist_by_id = graphene.Field(PlaylistType, playlist_id=graphene.String(required=True))

    all_videos = graphene.List(VideoType)
    video_by_id = graphene.Field(VideoType, video_id=graphene.String(required=True))

    def resolve_all_users(root, info):
        return CustomUserModel.objects.all()

    def resolve_user_by_id(root, info, user_id):
        try:
            return CustomUserModel.objects.get(pk=user_id)
        except CustomUserModel.DoesNotExist:
            return None

    def resolve_all_restricted_users(root, info):
        return RestrictedUserModel.objects.select_related('restricted_user').all()

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

    def resolve_playlist_by_id(root, info, playlist_id):
        return PlaylistModel.objects.prefetch_related('associated_profiles').filter(pk=playlist_id).first()

    def resolve_all_videos(root, info):
        return VideoModel.objects.prefetch_related('playlists').all()

    def resolve_video_by_id(root, info, video_id):
        return VideoModel.objects.prefetch_related('playlists').filter(pk=video_id).first()


schema = graphene.Schema(query=Query)