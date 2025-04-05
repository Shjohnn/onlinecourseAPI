from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status, serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny, BasePermission
from rest_framework.response import Response
from rest_framework.filters import SearchFilter, OrderingFilter

from .serializers import *
from .models import Course, Lesson, Payment, User


class IsInstructor(BasePermission):
    """
    Custom permission to only allow instructors to create or modify objects.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_instructor


class CoursePagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 100


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class CourseListCreateView(generics.ListCreateAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated, IsInstructor]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['price']
    search_fields = ['instructor__username']
    ordering_fields = ['price', 'rating']
    pagination_class = CoursePagination

    def create(self, request, *args, **kwargs):
        self.check_permissions(request)  # Permissionlarni tekshirish
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'message': 'Course successfully added', 'data': serializer.data}, status=status.HTTP_201_CREATED)


class CourseRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if serializer.instance.instructor != self.request.user:
            raise PermissionDenied(detail='You are not the owner of this course')
        serializer.save()
        return Response({'message': 'Course successfully updated'})

    def perform_destroy(self, instance):
        if instance.instructor != self.request.user:
            raise PermissionDenied(detail='You are not the owner of this course')
        instance.delete()
        return Response({'message': 'Course successfully deleted'})


class LessonListCreateView(generics.ListCreateAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response({'message': 'Lesson successfully added', 'data': serializer.data}, status=status.HTTP_201_CREATED)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        if serializer.instance.course.instructor != self.request.user:
            raise PermissionDenied(detail='You are not the owner of this lesson')
        serializer.save()
        return Response({'message': 'Lesson successfully updated'})

    def perform_destroy(self, instance):
        if instance.course.instructor != self.request.user:
            raise PermissionDenied(detail='You are not the owner of this lesson')
        instance.delete()
        return Response({'message': 'Lesson successfully deleted'})


class PaymentView(generics.ListCreateAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        amount = serializer.validated_data.get('amount')
        if not course or not amount:
            raise serializers.ValidationError({'error': 'Course or amount data is missing!'})
        if course.price > amount:
            raise serializers.ValidationError({'error': 'Payment amount is not sufficient!'})
        serializer.save(user=self.request.user)


class CourseEnrollView(generics.CreateAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id, *args, **kwargs):
        course = Course.objects.get(id=course_id)

        # Agar foydalanuvchi kursni sotib olmagan bo‘lsa, ruxsat yo‘q
        if not Payment.objects.filter(user=request.user, course=course).exists():
            raise PermissionDenied("You must purchase this course to enroll.")

        enrollment, created = Enrollment.objects.get_or_create(user=request.user, course=course)

        if created:
            return Response({"message": "Successfully enrolled in the course."}, status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "You are already enrolled in this course."}, status=status.HTTP_200_OK)


class CourseStudentsView(generics.ListAPIView):
    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        course = Course.objects.get(id=self.kwargs['course_id'])
        if course.instructor != self.request.user:
            raise PermissionDenied("Only the instructor can view the students.")
        return Enrollment.objects.filter(course=course)


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id, *args, **kwargs):
        course = Course.objects.get(id=course_id)
        if not Enrollment.objects.filter(user=request.user, course=course).exists():
            raise PermissionDenied("You must be enrolled in the course to leave a review.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user, course=course)
        return Response({"message": "Review successfully added."}, status=status.HTTP_201_CREATED)


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer

    def get_queryset(self):
        course = Course.objects.get(id=self.kwargs['course_id'])
        return Review.objects.filter(course=course)