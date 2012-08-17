from django.test import TestCase
from django.test.client import Client
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from mock import patch
from nose.tools import istest, assert_equal, assert_in
from ..models import Place, Submission, SubmissionSet
from ..views import SubmissionCollectionView
import json


class TestMakingAGetRequestToASubmissionTypeCollectionUrl (TestCase):

    @istest
    def should_call_view_with_place_id_and_submission_type_name(self):
        client = Client()

        with patch('sa_api.views.SubmissionCollectionView.get') as getter:
            client.get('/api/v1/places/1/comments/')
            args, kwargs = getter.call_args
            assert_equal(
                kwargs,
                {'place_id': u'1',
                 'submission_type': u'comments'}
            )

    @istest
    def should_return_a_list_of_submissions_of_the_type_for_the_place(self):
        Place.objects.all().delete()
        Submission.objects.all().delete()

        place = Place.objects.create(location='POINT(0 0)')
        comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')
        Submission.objects.create(parent_id=comments.id)
        Submission.objects.create(parent_id=comments.id)

        request = RequestFactory().get('/places/1/comments/')
        view = SubmissionCollectionView.as_view()

        response = view(request, place_id=1,
                        submission_type='comments')
        data = json.loads(response.content)
        assert_equal(len(data), 2)


    @istest
    def should_return_an_empty_list_if_the_place_has_no_submissions_of_the_type(self):
        Place.objects.all().delete()
        Submission.objects.all().delete()

        place = Place.objects.create(location='POINT(0 0)')
        comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')
        Submission.objects.create(parent_id=comments.id)
        Submission.objects.create(parent_id=comments.id)

        request = RequestFactory().get('/places/1/votes/')
        view = SubmissionCollectionView.as_view()

        response = view(request, place_id=1,
                        submission_type='votes')
        data = json.loads(response.content)
        assert_equal(len(data), 0)


class TestMakingAPostRequestToASubmissionTypeCollectionUrl (TestCase):

    @istest
    def should_create_a_new_submission_of_the_given_type_on_the_place(self):
        Place.objects.all().delete()
        Submission.objects.all().delete()
        SubmissionSet.objects.all().delete()

        place = Place.objects.create(location='POINT(0 0)')
        comments = SubmissionSet.objects.create(place_id=place.id, submission_type='comments')

        data = {
            'submitter_name': 'Mjumbe Poe',
            'age': 12,
            'comment': 'This is rad!',
        }
        request = RequestFactory().post('/places/1/comments/', data=json.dumps(data), content_type='application/json')
        view = SubmissionCollectionView.as_view()

        response = view(request, place_id=1,
                        submission_type='comments')
        data = json.loads(response.content)
        #print response
        assert_equal(response.status_code, 201)
        assert_in('age', data)


class TestSubmissionInstanceAPI (TestCase):

    def setUp(self):
        Place.objects.all().delete()
        Submission.objects.all().delete()
        SubmissionSet.objects.all().delete()

        self.place = Place.objects.create(location='POINT(0 0)')
        self.comments = SubmissionSet.objects.create(place_id=self.place.id,
                                                submission_type='comments')
        self.submission = Submission.objects.create(parent_id=self.comments.id)
        self.url = reverse('submission_instance',
                           kwargs=dict(place_id=self.place.id,
                                       pk=self.submission.id,
                                       submission_type='comments'))
        from ..views import SubmissionInstanceView
        self.view = SubmissionInstanceView.as_view()

    @istest
    def put_request_should_modify_instance(self):
        data = {
            'submitter_name': 'Paul Winkler',
            'age': 99,
            'comment': 'Get off my lawn!',
        }

        request = RequestFactory().put(self.url, data=json.dumps(data),
                                       content_type='application/json')

        response = self.view(request, place_id=self.place.id,
                             pk=self.submission.id,
                             submission_type='comments')
        response_data = json.loads(response.content)
        assert_equal(response.status_code, 200)
        self.assertDictContainsSubset(data, response_data)

    @istest
    def delete_request_should_delete_submission(self):
        request = RequestFactory().delete(self.url)
        response = self.view(request, place_id=self.place.id,
                             pk=self.submission.id,
                             submission_type='comments')

        assert_equal(response.status_code, 204)
        assert_equal(Submission.objects.all().count(), 0)

    @istest
    def submission_get_request_retrieves_data(self):
        self.submission.data = json.dumps({'animal': 'tree frog'})
        self.submission.save()
        request = RequestFactory().get(self.url)
        response = self.view(request, place_id=self.place.id,
                             pk=self.submission.id,
                             submission_type='comments')

        assert_equal(response.status_code, 200)
        data = json.loads(response.content)
        assert_equal(data['animal'], 'tree frog')
