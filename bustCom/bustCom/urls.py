from django.urls import path, include
from django.contrib import admin
from bustComProj.views import *

urlpatterns = [
    path('', home, name='home'),
    path('courses/', courses_list, name='courses_list'),
    path('course/create/', create_course, name='add_course'),  
    path('course/<int:course_id>/', course_detail, name='course_detail'),
    path('course/<int:course_id>/enroll/', enroll_course, name='enroll_course'),
    path('course/<int:course_id>/lectures/', course_lectures, name='course_lectures'),
    path('course/<int:course_id>/edit/', edit_course, name='edit_course'),
    path('course/<int:course_id>/delete/', delete_course, name='delete_course'),

    path('lecture/<int:lecture_id>/', lecture_detail, name='lecture_detail'),
    path('lecture/<int:lecture_id>/test/<int:test_id>/', lecture_test, name='lecture_test'),

    path('lecture/<int:lecture_id>/complete/', mark_lecture_complete, name='mark_lecture_complete'),

    path('register/', register, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('course/<int:course_id>/add-lecture/', add_lecture, name='add_lecture'),

    path('admin/', admin.site.urls),
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('admin-panel/backup/download/', download_backup, name='download_backup'),
    path('admin-panel/backup/restore/', restore_backup, name='restore_backup'),

    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit_profile'),

    path('training/test-difficulty/', test_difficulty, name='test_difficulty'),
    path('training/review-requests/', review_requests, name='review_requests'),
    path('training/create-plan/', create_training_plan, name='create_training_plan'),
    path('training/edit-plan/<int:plan_id>/', edit_training_plan, name='edit_training_plan'),
    path('training/conduct/', conduct_training, name='conduct_training'),

    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('dashboard/employee/', employee_dashboard, name='employee_dashboard'),
    path('dashboard/teacher/', teacher_dashboard, name='teacher_dashboard'),
    path('dashboard/hr/', hr_dashboard, name='hr_dashboard'),
    path('dashboard/training-manager/', training_manager_dashboard, name='training_manager_dashboard'),

    path('questions/answer/', answer_questions, name='answer_questions'),
    path('teacher/feedback/', view_feedback, name='view_feedback'),

    path('hr/assign-courses/', assign_courses, name='assign_courses'),
    path('hr/track-performance/', track_performance, name='track_performance'),
    path('hr/evaluate-training/', evaluate_training, name='evaluate_training'),
    path('hr/training-evaluation/', training_evaluation, name='training_evaluation'),
    path('hr/view-requests/', hr_view_requests, name='hr_view_requests'),
    path('hr/manage-employees/', manage_employees, name='manage_employees'),
    path('dashboard/hr/manage_employees/', manage_employees, name='manage_employees'),

    path('training-manager/employee-progress/', employee_progress, name='employee_progress'),

    path('service/', service, name='service'),


    path('lecture/<int:lecture_id>/add-test/', add_test, name='add_test'),
    path('lecture/<int:lecture_id>/edit/', edit_lecture, name='edit_lecture'),
    path('lecture/<int:lecture_id>/delete/', delete_lecture, name='delete_lecture'),


    path('manage/<str:table_name>/', manage_table, name='manage_table'),
    path('manage/<str:table_name>/add/', add_object, name='add_object'),
    path('manage/<str:table_name>/edit/<int:object_id>/', edit_object, name='edit_object'),
    path('manage/<str:table_name>/delete/<int:object_id>/', delete_object, name='delete_object'),

    path('test/<int:test_id>/add-question/', add_question, name='add_question'),
    path('question/<int:question_id>/add-answer/', add_answer, name='add_answer'),
    path('manage-users/', manage_users, name='manage_users'),
    path('training/start/', start_training, name='start_training'),
    path('my-certificates/', my_certificates, name='my_certificates'),
    path('view-certificates/', view_certificates, name='view_certificates'),
    path('certificate/<int:certificate_id>/view/', view_certificate, name='view_certificate'),
    path('certificate/<int:certificate_id>/download/', download_certificate, name='download_certificate'),

    path('employee/my-requests/', my_requests, name='my_requests'),

    path('add-lecture-material/', add_lecture_material, name='add_lecture_material'),  

    # Include the app's URLs
    path('', include('bustComProj.urls')),
]

