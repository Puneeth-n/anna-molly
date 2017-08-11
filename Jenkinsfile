pipeline {
  agent any
  stages {
    stage('foo') {
      steps {
        parallel(
          "foo": {
            echo 'foo'
            
          },
          "bar": {
            echo 'bar'
            
          }
        )
      }
    }
    stage('baz') {
      steps {
        echo 'baz'
      }
    }
  }
}