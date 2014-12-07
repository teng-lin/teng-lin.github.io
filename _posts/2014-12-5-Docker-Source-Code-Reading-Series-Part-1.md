---
layout: post
title: Docker Source Code Reading Series - Part 1
---
[Docker](http://www.docker.com/) is the most promising technology for software development and deployment in the last decade.

This is the first post of a seriers of blog posts that records my personal experience in diving into the docker source code. Hopefully, it will also help developers who are new to docker to have better understanding of the internals of the [docker source code](https://github.com/docker/docker/tree/release-1.3).

## Pre-requirement

### Basic concept
It is very important to familiar yourself with a few basic concepts.

1. [Layer](https://docs.docker.com/terms/layer)
2. [Image](https://docs.docker.com/terms/image/)
3. [Container](https://docs.docker.com/terms/container/)
4. [Registry](https://docs.docker.com/terms/registry/)
5. [Repository](https://docs.docker.com/terms/repository/)

## Docker Binary

Below code snippet extracted from [docker/docker.go](https://github.com/docker/docker/blob/release-1.3/docker/docker.go) is the main entry point of docker.

{% highlight go linenos %}

func main() {
	if reexec.Init() {
		return
	}

	flag.Parse()
	// FIXME: validate daemon flags here

	if *flVersion {
		showVersion()
		return
	}

	if *flLogLevel != "" {
		lvl, err := log.ParseLevel(*flLogLevel)
		if err != nil {
			log.Fatalf("Unable to parse logging level: %s", *flLogLevel)
		}
		initLogging(lvl)
	} else {
		initLogging(log.InfoLevel)
	}

	// -D, --debug, -l/--log-level=debug processing
	// When/if -D is removed this block can be deleted
	if *flDebug {
		os.Setenv("DEBUG", "1")
		initLogging(log.DebugLevel)
	}

	if len(flHosts) == 0 {
		defaultHost := os.Getenv("DOCKER_HOST")
		if defaultHost == "" || *flDaemon {
			// If we do not have a host, default to unix socket
			defaultHost = fmt.Sprintf("unix://%s", api.DEFAULTUNIXSOCKET)
		}
		defaultHost, err := api.ValidateHost(defaultHost)
		if err != nil {
			log.Fatal(err)
		}
		flHosts = append(flHosts, defaultHost)
	}

	if *flDaemon {
		mainDaemon()
		return
	}

	if len(flHosts) > 1 {
		log.Fatal("Please specify only one -H")
	}
	protoAddrParts := strings.SplitN(flHosts[0], "://", 2)

	var (
		cli       *client.DockerCli
		tlsConfig tls.Config
	)
	tlsConfig.InsecureSkipVerify = true

	// Regardless of whether the user sets it to true or false, if they
	// specify --tlsverify at all then we need to turn on tls
	if flag.IsSet("-tlsverify") {
		*flTls = true
	}

	// If we should verify the server, we need to load a trusted ca
	if *flTlsVerify {
		certPool := x509.NewCertPool()
		file, err := ioutil.ReadFile(*flCa)
		if err != nil {
			log.Fatalf("Couldn't read ca cert %s: %s", *flCa, err)
		}
		certPool.AppendCertsFromPEM(file)
		tlsConfig.RootCAs = certPool
		tlsConfig.InsecureSkipVerify = false
	}

	// If tls is enabled, try to load and send client certificates
	if *flTls || *flTlsVerify {
		_, errCert := os.Stat(*flCert)
		_, errKey := os.Stat(*flKey)
		if errCert == nil && errKey == nil {
			*flTls = true
			cert, err := tls.LoadX509KeyPair(*flCert, *flKey)
			if err != nil {
				log.Fatalf("Couldn't load X509 key pair: %s. Key encrypted?", err)
			}
			tlsConfig.Certificates = []tls.Certificate{cert}
		}
		// Avoid fallback to SSL protocols < TLS1.0
		tlsConfig.MinVersion = tls.VersionTLS10
	}

	if *flTls || *flTlsVerify {
		cli = client.NewDockerCli(os.Stdin, os.Stdout, os.Stderr, nil, protoAddrParts[0], protoAddrParts[1], &tlsConfig)
	} else {
		cli = client.NewDockerCli(os.Stdin, os.Stdout, os.Stderr, nil, protoAddrParts[0], protoAddrParts[1], nil)
	}

	if err := cli.Cmd(flag.Args()...); err != nil {
		if sterr, ok := err.(*utils.StatusError); ok {
			if sterr.Status != "" {
				log.Println(sterr.Status)
			}
			os.Exit(sterr.StatusCode)
		}
		log.Fatal(err)
	}
}

{% endhighlight %}


`docker` has a monolithic binary, which contains both daemon (see line 45) and client (see line 100). Majority of the statements above are dealing with TLS security. However, there are a few things worth discussion.

* DOCKER_HOST (see line 32)

By default, docker daemon will listen on `unix:///var/run/docker.sock` to allow only local connections by the root user or the user in docker group. It can also listen on TCP port by setting DOCKER_HOST to `tcp://host:2375` or using `-H tcp://host:2375`, but this is not recommended due to security concern.

* Docker client (see line 95)
Docker client API source code can be found under api/client/
### Docker Daemon

[daemon/daemon.go](https://github.com/docker/docker/blob/release-1.3/daemon/daemon.go)

{% highlight go linenos %}
// +build daemon

package main

import (
	log "github.com/Sirupsen/logrus"
	"github.com/docker/docker/builder"
	"github.com/docker/docker/builtins"
	"github.com/docker/docker/daemon"
	_ "github.com/docker/docker/daemon/execdriver/lxc"
	_ "github.com/docker/docker/daemon/execdriver/native"
	"github.com/docker/docker/dockerversion"
	"github.com/docker/docker/engine"
	flag "github.com/docker/docker/pkg/mflag"
	"github.com/docker/docker/pkg/signal"
	"github.com/docker/docker/registry"
)

const CanDaemon = true

var (
	daemonCfg = &daemon.Config{}
)

func init() {
	daemonCfg.InstallFlags()
}

func mainDaemon() {
	if flag.NArg() != 0 {
		flag.Usage()
		return
	}
	eng := engine.New()
	signal.Trap(eng.Shutdown)

	daemonCfg.TrustKeyPath = *flTrustKey

	// Load builtins
	if err := builtins.Register(eng); err != nil {
		log.Fatal(err)
	}

	// load registry service
	if err := registry.NewService(daemonCfg.InsecureRegistries).Install(eng); err != nil {
		log.Fatal(err)
	}

	// load the daemon in the background so we can immediately start
	// the http api so that connections don't fail while the daemon
	// is booting
	go func() {
		d, err := daemon.NewDaemon(daemonCfg, eng)
		if err != nil {
			log.Fatal(err)
		}
		log.Infof("docker daemon: %s %s; execdriver: %s; graphdriver: %s",
			dockerversion.VERSION,
			dockerversion.GITCOMMIT,
			d.ExecutionDriver().Name(),
			d.GraphDriver().String(),
		)

		if err := d.Install(eng); err != nil {
			log.Fatal(err)
		}

		b := &builder.BuilderJob{eng, d}
		b.Install()

		// after the daemon is done setting up we can tell the api to start
		// accepting connections
		if err := eng.Job("acceptconnections").Run(); err != nil {
			log.Fatal(err)
		}
	}()

	// Serve api
	job := eng.Job("serveapi", flHosts...)
	job.SetenvBool("Logging", true)
	job.SetenvBool("EnableCors", *flEnableCors)
	job.Setenv("Version", dockerversion.VERSION)
	job.Setenv("SocketGroup", *flSocketGroup)

	job.SetenvBool("Tls", *flTls)
	job.SetenvBool("TlsVerify", *flTlsVerify)
	job.Setenv("TlsCa", *flCa)
	job.Setenv("TlsCert", *flCert)
	job.Setenv("TlsKey", *flKey)
	job.SetenvBool("BufferRequests", true)
	if err := job.Run(); err != nil {
		log.Fatal(err)
	}
}

{% endhighlight %}
### Docker client
