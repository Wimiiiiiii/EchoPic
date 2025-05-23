document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const resultsDiv = document.getElementById('results');
    const resultImages = document.getElementById('resultImages');
    const metricsList = document.getElementById('metrics');

    if (searchForm) {
        searchForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            // Afficher le loader
            const loader = document.createElement('div');
            loader.className = 'loading';
            loader.innerHTML = '<div class="loading-spinner"></div>';
            document.body.appendChild(loader);

            const formData = new FormData(searchForm);
            
            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (response.ok) {
                    // Afficher les résultats
                    resultsDiv.classList.remove('d-none');
                    displayResults(data);
                } else {
                    alert('Erreur: ' + data.error);
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Une erreur est survenue lors de la recherche');
            } finally {
                // Supprimer le loader
                document.body.removeChild(loader);
            }
        });
    }

    function displayResults(data) {
        // Vider les conteneurs
        resultImages.innerHTML = '';
        metricsList.innerHTML = '';

        // Afficher les images
        if (data.results && data.results.length > 0) {
            data.results.forEach(result => {
                const imgContainer = document.createElement('div');
                imgContainer.className = 'col-md-3 mb-3';
                imgContainer.innerHTML = `
                    <div class="card">
                        <img src="${result.image_url}" class="card-img-top" alt="Résultat">
                        <div class="card-body">
                            <p class="card-text">Similarité: ${(result.similarity * 100).toFixed(2)}%</p>
                        </div>
                    </div>
                `;
                resultImages.appendChild(imgContainer);
            });
        }

        // Afficher les métriques
        if (data.metrics) {
            Object.entries(data.metrics).forEach(([key, value]) => {
                const li = document.createElement('li');
                li.className = 'list-group-item metrics-item';
                li.innerHTML = `<strong>${key}:</strong> ${(value * 100).toFixed(2)}%`;
                metricsList.appendChild(li);
            });
        }

        // Afficher le graphique de précision/rappel si disponible
        if (data.precision_recall) {
            const ctx = document.getElementById('precisionRecallChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.precision_recall.recall,
                    datasets: [{
                        label: 'Précision',
                        data: data.precision_recall.precision,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 1
                        },
                        x: {
                            beginAtZero: true,
                            max: 1
                        }
                    }
                }
            });
        }
    }
}); 