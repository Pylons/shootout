import unittest

class ViewTests(unittest.TestCase):
    def setUp(self):
        # This sets up the application registry with the registrations
        # your application declares in its configure.zcml (including
        # dependent registrations for repoze.bfg itself).  This is a
        # heavy-hammer way of making sure that your tests have enough
        # context to run properly.  But tests will run faster if you
        # use only the registrations you need programmatically, so you
        # should explore ways to do that rather than rely on ZCML (see
        # the repoze.bfg tests for inspiration).
        self._cleanup()
        import repoze.shootout
        import zope.configuration.xmlconfig
        zope.configuration.xmlconfig.file('configure.zcml',
                                          package=repoze.shootout)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        # this clears the application registry 
        from zope.testing.cleanup import cleanUp
        cleanUp()
        
    def test_my_view(self):
        from repoze.shootout.views import my_view
        context = DummyContext()
        request = DummyRequest()
        result = my_view(context, request)
        self.assertEqual(result.status, '200 OK')
        body = result.app_iter[0]
        self.failUnless('Welcome to range' in body)
        self.assertEqual(len(result.headerlist), 2)
        self.assertEqual(result.headerlist[0],
                         ('content-type', 'text/html; charset=UTF-8'))
        self.assertEqual(result.headerlist[1], ('Content-Length',
                                                str(len(body))))

class DummyContext:
    pass

class DummyRequest:
    pass
